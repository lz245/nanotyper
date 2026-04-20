"""
Per-sample MLST call.

Inputs (provided by Snakemake):
    input.blast_tsvs : list of 7 BLAST TSVs (outfmt 6 + qlen slen), one per locus
    input.coverage   : cutadapt coverage TSV (locus, fwd, rev, both)
    input.profiles   : PubMLST profile table
Output:
    output.call_tsv : one-row TSV with columns
        sample_id, ST, adk, fumC, gyrB, icd, mdh, purA, recA,
        <locus>_identity, <locus>_coverage, <locus>_flag, qc_label, qc_notes

QC tiers (priority: FAIL > LOW_COVERAGE > NEW_ALLELE > NEW_ST > PASS):
    FAIL         : any locus coverage < coverage_warn OR no BLAST hit OR no consensus
    LOW_COVERAGE : any locus coverage_warn <= cov < coverage_good (but allele called)
    NEW_ALLELE   : any locus BLAST %id < min_identity OR not full-length
    NEW_ST       : all 7 loci have known alleles but combo not in profiles
    PASS         : all 7 loci known alleles, full-length, full coverage, combo in profiles
"""
import sys
import pandas as pd
from pathlib import Path

# ---- Snakemake-injected objects ----
blast_tsvs   = list(snakemake.input.blast_tsvs)
coverage_tsv = snakemake.input.coverage
profiles_txt = snakemake.input.profiles
output_tsv   = snakemake.output.call_tsv
sample       = snakemake.wildcards.sample
loci         = list(snakemake.params.loci)
min_identity = float(snakemake.params.min_identity)
require_full = bool(snakemake.params.require_full)
cov_good     = float(snakemake.params.coverage_good)
cov_warn     = float(snakemake.params.coverage_warn)

BLAST_COLS = [
    "qseqid","sseqid","pident","length","mismatch","gapopen",
    "qstart","qend","sstart","send","evalue","bitscore","qlen","slen",
]

def parse_allele_id(sseqid: str) -> str:
    """PubMLST allele IDs look like 'adk_42' or 'adk-42'. Extract the integer tail."""
    for sep in ("_", "-"):
        if sep in sseqid:
            tail = sseqid.rsplit(sep, 1)[1]
            if tail.isdigit():
                return tail
    # fallback: last run of digits
    digits = "".join(c for c in sseqid if c.isdigit())
    return digits or sseqid


def call_locus(blast_path: Path):
    """Return (allele, pident, length, flag) for one locus. flag in {known,new_allele,no_hit}."""
    if not Path(blast_path).exists() or Path(blast_path).stat().st_size == 0:
        return ("-", 0.0, 0, "no_hit")
    df = pd.read_csv(blast_path, sep="\t", names=BLAST_COLS)
    if df.empty:
        return ("-", 0.0, 0, "no_hit")
    # Best hit: highest bitscore
    best = df.sort_values("bitscore", ascending=False).iloc[0]
    pident = float(best["pident"])
    slen   = int(best["slen"])
    length = int(best["length"])
    full_len = (length == slen)
    known = (pident >= min_identity) and ((not require_full) or full_len)
    if known:
        return (parse_allele_id(str(best["sseqid"])), pident, length, "known")
    else:
        return (parse_allele_id(str(best["sseqid"])), pident, length, "new_allele")


def load_coverage(path: str) -> dict:
    """Return {locus: coverage_count} from cutadapt coverage TSV."""
    cov_df = pd.read_csv(path, sep="\t")
    # Columns expected: locus, fwd, rev, both
    return dict(zip(cov_df["locus"], cov_df["both"].astype(float)))


def lookup_st(profiles_path: str, allele_row: dict, loci_order: list) -> str:
    """Look up ST from profiles.txt given {locus: allele_id}. Returns ST or 'new_ST'."""
    prof = pd.read_csv(profiles_path, sep="\t", dtype=str)
    mask = pd.Series([True] * len(prof))
    for locus in loci_order:
        mask &= (prof[locus] == str(allele_row[locus]))
    hit = prof[mask]
    if len(hit) == 1:
        return str(hit.iloc[0]["ST"])
    return "new_ST"


def main():
    # 1) BLAST-based allele calls
    calls = {}
    for locus in loci:
        # Match each blast tsv to its locus by filename
        matching = [p for p in blast_tsvs if p.endswith(f"_{locus}.tsv")]
        if not matching:
            calls[locus] = ("-", 0.0, 0, "no_hit")
        else:
            calls[locus] = call_locus(matching[0])

    # 2) Coverage lookup
    cov_map = load_coverage(coverage_tsv)
    cov_per_locus = {l: cov_map.get(l, 0.0) for l in loci}

    # 3) Decide QC label
    flags = {l: calls[l][3] for l in loci}
    qc_notes = []

    has_no_hit = any(flags[l] == "no_hit" for l in loci)
    any_low_cov = any(cov_per_locus[l] < cov_warn for l in loci)
    any_mid_cov = any(cov_warn <= cov_per_locus[l] < cov_good for l in loci)
    any_new_allele = any(flags[l] == "new_allele" for l in loci)
    all_known = all(flags[l] == "known" for l in loci)

    # Attempt ST lookup whenever all 7 alleles are called as "known", regardless
    # of coverage. This lets the user see a tentative ST even when QC = FAIL.
    if all_known:
        allele_row = {l: calls[l][0] for l in loci}
        st = lookup_st(profiles_txt, allele_row, loci)
    else:
        st = "-"

    # QC label (priority: FAIL > LOW_COVERAGE > NEW_ALLELE > NEW_ST > PASS)
    if has_no_hit or any_low_cov:
        qc_label = "FAIL"
        if has_no_hit:
            qc_notes.append("missing_locus:" + ",".join(l for l in loci if flags[l] == "no_hit"))
        if any_low_cov:
            qc_notes.append("low_cov:" + ",".join(l for l in loci if cov_per_locus[l] < cov_warn))
    elif any_mid_cov:
        qc_label = "LOW_COVERAGE"
        qc_notes.append("mid_cov:" + ",".join(l for l in loci if cov_warn <= cov_per_locus[l] < cov_good))
    elif any_new_allele:
        qc_label = "NEW_ALLELE"
        qc_notes.append("new_allele:" + ",".join(l for l in loci if flags[l] == "new_allele"))
    elif st == "new_ST":
        qc_label = "NEW_ST"
    else:
        qc_label = "PASS"

    # 4) Build single-row output
    row = {"sample_id": sample, "ST": st}
    for l in loci:
        row[l] = calls[l][0]
    for l in loci:
        row[f"{l}_identity"] = round(calls[l][1], 2)
    for l in loci:
        row[f"{l}_coverage"] = int(cov_per_locus[l])
    for l in loci:
        row[f"{l}_flag"] = flags[l]
    row["qc_label"] = qc_label
    row["qc_notes"] = ";".join(qc_notes)

    Path(output_tsv).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(output_tsv, sep="\t", index=False)


if __name__ == "__main__":
    main()
