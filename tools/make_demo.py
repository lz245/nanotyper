#!/usr/bin/env python3
"""
Build (or rebuild) the nanotyper demo dataset by deterministic subsampling.

USAGE
    tools/make_demo.py                     # rebuild test/demo/fastq_pass/ from the manifest
    tools/make_demo.py --manifest FILE     # use another manifest

The manifest (test/demo/manifest.tsv) has one row per demo barcode:
    barcode  source_dir  n_reads  seed
Reads from every *.fastq.gz in source_dir are pooled, n_reads are drawn
without replacement with random.Random(seed) (all reads if fewer exist), and
written to test/demo/fastq_pass/<barcode>/<barcode>_demo.fastq.gz.

This script exists so the demo is reproducible from the lab's raw data; users
of the pipeline never need to run it.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DEMO = HERE / "test" / "demo"


def read_records(fastq_gz: Path):
    with gzip.open(fastq_gz, "rt") as fh:
        while True:
            rec = [fh.readline() for _ in range(4)]
            if not rec[0]:
                return
            if not rec[3]:
                sys.exit(f"ERROR: truncated record in {fastq_gz}")
            yield "".join(rec)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=DEMO / "manifest.tsv")
    ap.add_argument("--out", type=Path, default=DEMO / "fastq_pass")
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.manifest), delimiter="\t"))
    for r in rows:
        src = Path(r["source_dir"]).expanduser()
        files = sorted(src.glob("*.fastq.gz"))
        if not files:
            sys.exit(f"ERROR: no *.fastq.gz in {src}")
        pool = [rec for f in files for rec in read_records(f)]
        n = min(int(r["n_reads"]), len(pool))
        picked = random.Random(int(r["seed"])).sample(pool, n) if n < len(pool) else pool
        out_dir = a.out / r["barcode"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{r['barcode']}_demo.fastq.gz"
        with gzip.open(out, "wt", compresslevel=9) as fh:
            fh.writelines(picked)
        print(f"{r['barcode']}: {n:5d} of {len(pool):5d} reads (seed {r['seed']}) -> {out} ({out.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
