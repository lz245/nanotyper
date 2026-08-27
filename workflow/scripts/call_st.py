"""
Per-sample MLST call.

Inputs (provided by Snakemake):
    input.blast_tsvs : list of BLAST TSVs (outfmt 6 + qlen slen), one per locus
    input.coverage   : cutadapt coverage TSV (locus, fwd, rev, both)
    input.profiles   : PubMLST profile table
Output:
    output.call_tsv : one-row TSV with columns
        sample_id, ST, <locus>..., <locus>_identity, <locus>_coverage, <locus>_flag,
        qc_label, qc_notes

QC tiers (priority: FAIL > LOW_COVERAGE > NEW_ALLELE > NEW_ST > PASS):
    FAIL         : any locus coverage < coverage_warn OR no BLAST hit OR no consensus
    LOW_COVERAGE : any locus coverage_warn <= cov < coverage_good (but allele called)
    NEW_ALLELE   : any locus BLAST %id < min_identity OR not full-length
    NEW_ST       : all loci have known alleles but combo not in profiles
    PASS         : all loci known alleles, full-length, full coverage, combo in profiles

The functions below are pure (no Snakemake state) so test/test_call_st.py can
import and exercise them; main() is the only place that reads `snakemake`.
"""
from pathlib import Path

import pandas as pd

BLAST_COLS = [
    "qseqid", "sseqid", "pident", "length", "mismatch", "gapopen",
    "qstart", "qend", "sstart", "send", "evalue", "bitscore", "qlen", "slen",
]

QC_PRIORITY = ("FAIL", "LOW_COVERAGE", "NEW_ALLELE", "NEW_ST", "PASS")


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


def call_locus(blast_path, min_identity: float, require_full: bool):
    """Return (allele, pident, length, flag) for one locus. flag in {known,new_allele,no_hit}."""
    blast_path = Path(blast_path)
    if not blast_path.exists() or blast_path.stat().st_size == 0:
        return ("-", 0.0, 0, "no_hit")
    df = pd.read_csv(blast_path, sep="\t", names=BLAST_COLS)
    if df.empty:
        return ("-", 0.0, 0, "no_hit")
    # Best hit: highest bitscore
    best = df.sort_values("bitscore", ascending=False).iloc[0]
    pident = float(best["pident"])
    slen = int(best["slen"])
    length = int(best["length"])
    full_len = length == slen
    known = (pident >= min_identity) and ((not require_full) or full_len)
    flag = "known" if known else "new_allele"
    return (parse_allele_id(str(best["sseqid"])), pident, length, flag)


def load_coverage(path) -> dict:
    """Return {locus: both-primer read count} from the cutadapt coverage TSV."""
    cov_df = pd.read_csv(path, sep="\t")
    return dict(zip(cov_df["locus"], cov_df["both"].astype(float)))


def lookup_st(profiles_path, allele_row: dict, loci_order: list) -> str:
    """Look up ST from profiles.txt given {locus: allele_id}. Returns ST or 'new_ST'."""
    prof = pd.read_csv(profiles_path, sep="\t", dtype=str)
    mask = pd.Series([True] * len(prof))
    for locus in loci_order:
        mask &= prof[locus] == str(allele_row[locus])
    hit = prof[mask]
    if len(hit) == 1:
        return str(hit.iloc[0]["ST"])
    return "new_ST"


def assign_qc(flags: dict, cov_per_locus: dict, loci: list, cov_warn: float, cov_good: float, st: str):
    """Return (qc_label, qc_notes) from per-locus flags, coverages, and the ST lookup result."""
    notes = []
    has_no_hit = any(flags[l] == "no_hit" for l in loci)
    any_low_cov = any(cov_per_locus[l] < cov_warn for l in loci)
    any_mid_cov = any(cov_warn <= cov_per_locus[l] < cov_good for l in loci)
    any_new_allele = any(flags[l] == "new_allele" for l in loci)

    if has_no_hit or any_low_cov:
        label = "FAIL"
        if has_no_hit:
            notes.append("missing_locus:" + ",".join(l for l in loci if flags[l] == "no_hit"))
        if any_low_cov:
            notes.append("low_cov:" + ",".join(l for l in loci if cov_per_locus[l] < cov_warn))
    elif any_mid_cov:
        label = "LOW_COVERAGE"
        notes.append("mid_cov:" + ",".join(l for l in loci if cov_warn <= cov_per_locus[l] < cov_good))
    elif any_new_allele:
        label = "NEW_ALLELE"
        notes.append("new_allele:" + ",".join(l for l in loci if flags[l] == "new_allele"))
    elif st == "new_ST":
        label = "NEW_ST"
    else:
        label = "PASS"
    return label, ";".join(notes)


def call_sample(sample: str, blast_tsvs: list, coverage_tsv, profiles_txt, loci: list,
                min_identity: float, require_full: bool, cov_good: float, cov_warn: float) -> dict:
    """Full per-sample call: returns the one-row dict written to the call TSV."""
    calls = {}
    for locus in loci:
        matching = [p for p in blast_tsvs if str(p).endswith(f"_{locus}.tsv")]
        calls[locus] = call_locus(matching[0], min_identity, require_full) if matching else ("-", 0.0, 0, "no_hit")

    cov_map = load_coverage(coverage_tsv)
    cov_per_locus = {l: cov_map.get(l, 0.0) for l in loci}
    flags = {l: calls[l][3] for l in loci}

    # Attempt ST lookup whenever all alleles are "known", regardless of coverage,
    # so the user sees a tentative ST even when QC = FAIL.
    if all(flags[l] == "known" for l in loci):
        st = lookup_st(profiles_txt, {l: calls[l][0] for l in loci}, loci)
    else:
        st = "-"

    qc_label, qc_notes = assign_qc(flags, cov_per_locus, loci, cov_warn, cov_good, st)

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
    row["qc_notes"] = qc_notes
    return row


def main():
    row = call_sample(
        sample=snakemake.wildcards.sample,
        blast_tsvs=list(snakemake.input.blast_tsvs),
        coverage_tsv=snakemake.input.coverage,
        profiles_txt=snakemake.input.profiles,
        loci=list(snakemake.params.loci),
        min_identity=float(snakemake.params.min_identity),
        require_full=bool(snakemake.params.require_full),
        cov_good=float(snakemake.params.coverage_good),
        cov_warn=float(snakemake.params.coverage_warn),
    )
    out = Path(snakemake.output.call_tsv)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([row]).to_csv(out, sep="\t", index=False)


if __name__ == "__main__":
    main()
