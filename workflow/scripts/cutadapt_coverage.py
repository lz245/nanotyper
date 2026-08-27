"""
Per-sample primer-coverage QC via cutadapt.

For each locus: count reads containing the forward primer, the reverse primer,
and both (anchored linked-adapter search). Output:
    locus  fwd  rev  both

We invoke cutadapt three times per locus (fwd only, rev only, linked) because
cutadapt's 'read count' is most reliably obtained from the JSON report.
"""
import json
import subprocess
from pathlib import Path
import pandas as pd

# ---- Snakemake-injected ----
fastq_in    = snakemake.input.fastq
primers_csv = snakemake.input.primers
output_tsv  = snakemake.output.tsv
loci        = list(snakemake.params.loci)
error_rate  = float(snakemake.params.error_rate)
log_path    = snakemake.log[0]

LOG = open(log_path, "w")


def log(msg: str):
    print(msg, file=LOG, flush=True)


def load_primers(path: str) -> dict:
    """Return {locus: (fwd, rev)} from primers.csv (columns: gene, Orientation, Sequence)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    fwd_map = df[df["orientation"].str.lower() == "forward"].set_index(
        df.columns[0])["sequence"].to_dict()
    rev_map = df[df["orientation"].str.lower() == "reverse"].set_index(
        df.columns[0])["sequence"].to_dict()
    # Handle possible leading/trailing whitespace in the gene column
    fwd_map = {k.strip(): v.strip() for k, v in fwd_map.items()}
    rev_map = {k.strip(): v.strip() for k, v in rev_map.items()}
    return {l: (fwd_map.get(l), rev_map.get(l)) for l in fwd_map.keys() | rev_map.keys()}


def run_cutadapt(cmd_args: list, fastq: str, tag: str, outdir: Path) -> int:
    """Run cutadapt with given adapter flags, return count of reads that matched
    ALL specified adapters (reads passing --discard-untrimmed)."""
    json_out = outdir / f"{tag}.json"
    cmd = [
        "cutadapt",
        "-e", str(error_rate),
        "--discard-untrimmed",
        "--json", str(json_out),
        "-o", "/dev/null",
    ] + cmd_args + [fastq]
    log(f"$ {' '.join(cmd)}")
    rc = subprocess.run(cmd, stdout=LOG, stderr=LOG).returncode
    if rc != 0:
        raise RuntimeError(f"cutadapt failed for tag {tag} (rc={rc})")
    with open(json_out) as fh:
        report = json.load(fh)
    # With --discard-untrimmed, output_read_count = reads passing (matched).
    return int(report["read_counts"].get("output", report["read_counts"].get("output_read_count", 0)))


def main():
    primers = load_primers(primers_csv)
    outdir = Path(output_tsv).parent / "cutadapt_tmp"
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for locus in loci:
        fwd, rev = primers.get(locus, (None, None))
        if not fwd or not rev:
            log(f"WARN: missing primers for {locus}; writing zeros")
            rows.append({"locus": locus, "fwd": 0, "rev": 0, "both": 0})
            continue
        # fwd primer at 5' end (-g), rev primer at 3' end (-a). Matches the
        # old pipeline's 12_analyze_locus_coverage_cutadapt.sh behavior.
        fwd_count  = run_cutadapt(["-g", fwd],              fastq_in, f"{locus}_fwd",  outdir)
        rev_count  = run_cutadapt(["-a", rev],              fastq_in, f"{locus}_rev",  outdir)
        both_count = run_cutadapt(["-g", fwd, "-a", rev],   fastq_in, f"{locus}_both", outdir)
        rows.append({"locus": locus, "fwd": fwd_count, "rev": rev_count, "both": both_count})
        log(f"{locus}: fwd={fwd_count} rev={rev_count} both={both_count}")

    pd.DataFrame(rows).to_csv(output_tsv, sep="\t", index=False)
    log(f"wrote {output_tsv}")


if __name__ == "__main__":
    try:
        main()
    finally:
        LOG.close()
