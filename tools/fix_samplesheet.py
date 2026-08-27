#!/usr/bin/env python3
"""
Lint and auto-fix nanotyper samplesheets.

Detects duplicate sample_id values and, in --write mode, rewrites them
as `<sample_id>_<barcode>`, preserving the original in a `biological_id`
column so replicate groups remain linked.

Why: sample_id must be unique because it's the result directory name.
When a sheet has repeated placeholders like "Unknown" or genuine
technical replicates sharing an ID, the pipeline refuses to start.
This utility unambiguously disambiguates without losing information.

Usage:
    # scan only (exit 0 if clean, 1 if problems found)
    tools/fix_samplesheet.py --check <samplesheet.csv> [<samplesheet.csv> ...]

    # auto-fix in place; originals backed up to *.bak
    tools/fix_samplesheet.py --write <samplesheet.csv> [<samplesheet.csv> ...]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List

import pandas as pd


def inspect(df: pd.DataFrame) -> dict:
    """Return a dict describing any issues found in df."""
    issues = {}
    if "sample_id" not in df.columns:
        issues["missing_column"] = "sample_id"
        return issues
    dupes = df["sample_id"][df["sample_id"].duplicated(keep=False)].unique().tolist()
    if dupes:
        issues["duplicate_sample_id"] = sorted(dupes)
    # (run_id, barcode) collisions are also bugs
    if {"run_id", "barcode"}.issubset(df.columns):
        key_dupes = (
            df.groupby(["run_id", "barcode"]).size().reset_index(name="n")
              .query("n > 1")
        )
        if not key_dupes.empty:
            issues["duplicate_run_barcode"] = [
                f"(run_id={r.run_id}, barcode={r.barcode})"
                for _, r in key_dupes.iterrows()
            ]
    return issues


def fix(df: pd.DataFrame) -> pd.DataFrame:
    """Disambiguate duplicate sample_id by appending _<barcode>.
    Preserves the original sample_id in biological_id (creating the column
    if absent, filling only the affected rows — other rows stay untouched)."""
    dupes = df["sample_id"][df["sample_id"].duplicated(keep=False)].unique()
    if len(dupes) == 0:
        return df
    if "biological_id" not in df.columns:
        df["biological_id"] = pd.NA
    mask = df["sample_id"].isin(dupes)
    # Only fill biological_id where it's currently empty (preserve user-set values)
    df.loc[mask, "biological_id"] = (
        df.loc[mask, "biological_id"].fillna(df.loc[mask, "sample_id"])
    )
    df.loc[mask, "sample_id"] = (
        df.loc[mask, "sample_id"].astype(str) + "_" + df.loc[mask, "barcode"].astype(str)
    )
    return df


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Report issues; exit 1 if any. Does not modify files.")
    mode.add_argument("--write", action="store_true",
                      help="Auto-fix duplicates and overwrite each file (backup as .bak).")
    ap.add_argument("samplesheets", nargs="+", help="One or more samplesheet.csv paths")
    args = ap.parse_args(argv)

    any_issue = False
    for path_str in args.samplesheets:
        p = Path(path_str)
        if not p.exists():
            print(f"  {p}: NOT FOUND", file=sys.stderr)
            any_issue = True
            continue
        df = pd.read_csv(p)
        issues = inspect(df)
        label = p.parent.name or p.name
        if not issues:
            print(f"  {label}: ok")
            continue
        any_issue = True
        for kind, details in issues.items():
            print(f"  {label}: {kind}: {details}")
        if args.write:
            if "missing_column" in issues:
                print(f"  {label}: cannot auto-fix (missing column); skipping write")
                continue
            shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))
            fix(df).to_csv(p, index=False)
            print(f"  {label}: fixed -> {p} (backup: {p.name}.bak)")

    if args.check and any_issue:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
