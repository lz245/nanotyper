#!/usr/bin/env python3
"""
Cross-run aggregator for ONT-MLST.

Concatenates every per-run mlst_summary.tsv into one wide table, then
produces:
    combined_summary.tsv    one row per sample across all runs, with run_folder column
    combined_summary.xlsx   (if openpyxl is installed) same data with QC-coloured rows
    st_distribution.tsv     ST × run_folder pivot (how often each ST appears per run)
    qc_by_run.tsv           QC label × run_folder pivot
    replicates.tsv          biological_id × ST groups that disagree (if biological_id used)
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

QC_BG = {
    "PASS":         "E8F5E9",
    "NEW_ST":       "FFF8E1",
    "LOW_COVERAGE": "FFF1E0",
    "NEW_ALLELE":   "FCE4EC",
    "FAIL":         "FFEBEE",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis-root", type=Path, required=True,
                    help="(informational) root of per-run analyses")
    ap.add_argument("--output", type=Path, required=True,
                    help="directory to write combined outputs into")
    ap.add_argument("summaries", nargs="+",
                    help="paths to per-run mlst_summary.tsv files")
    args = ap.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    # --- load and tag each per-run summary ---
    frames = []
    for p in args.summaries:
        p = Path(p)
        # analysis folder name = 2 levels up (…/<run>/results/mlst_summary.tsv)
        run_folder = p.parent.parent.name
        df = pd.read_csv(p, sep="\t", dtype=str)
        df.insert(0, "run_folder", run_folder)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # --- 1) combined wide summary ---
    tsv_path = args.output / "combined_summary.tsv"
    combined.to_csv(tsv_path, sep="\t", index=False)
    print(f"  wrote {tsv_path}  ({len(combined):,} rows, {len(args.summaries)} runs)")

    # --- 2) xlsx with QC-coloured rows ---
    try:
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Font
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "Combined"

        for col_idx, col in enumerate(combined.columns, 1):
            c = ws.cell(row=1, column=col_idx, value=col)
            c.font = Font(bold=True)

        qc_col = combined.columns.get_loc("qc_label") + 1 if "qc_label" in combined.columns else None
        for r_idx, (_, row) in enumerate(combined.iterrows(), 2):
            fill = None
            if qc_col is not None:
                qc = row.get("qc_label", "")
                if qc in QC_BG:
                    fill = PatternFill("solid", fgColor=QC_BG[qc])
            for c_idx, col in enumerate(combined.columns, 1):
                val = row[col]
                cell = ws.cell(row=r_idx, column=c_idx, value="" if pd.isna(val) else val)
                if fill is not None:
                    cell.fill = fill

        for col_idx, col in enumerate(combined.columns, 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = \
                max(12, min(30, len(str(col)) + 2))
        ws.freeze_panes = "A2"

        xlsx_path = args.output / "combined_summary.xlsx"
        wb.save(xlsx_path)
        print(f"  wrote {xlsx_path}")
    except ImportError:
        print("  (openpyxl not installed — skipped .xlsx output)")

    # --- 3) ST × run pivot ---
    if "ST" in combined.columns:
        called = combined[combined["ST"].astype(str).ne("-") & combined["ST"].notna()].copy()
        if not called.empty:
            pivot = (called.groupby(["ST", "run_folder"]).size()
                           .unstack(fill_value=0)
                           .sort_index())
            pivot["_total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values("_total", ascending=False)
            pivot_path = args.output / "st_distribution.tsv"
            pivot.to_csv(pivot_path, sep="\t")
            print(f"  wrote {pivot_path}  ({len(pivot)} unique STs)")

    # --- 4) QC summary per run ---
    if "qc_label" in combined.columns:
        qc = (combined.groupby(["run_folder", "qc_label"]).size()
                      .unstack(fill_value=0)
                      .reindex(columns=["PASS","NEW_ST","LOW_COVERAGE","NEW_ALLELE","FAIL"],
                               fill_value=0))
        qc["total"] = qc.sum(axis=1)
        qc_path = args.output / "qc_by_run.tsv"
        qc.to_csv(qc_path, sep="\t")
        print(f"  wrote {qc_path}")
        print("\n  QC label counts by run:")
        print(qc.to_string().replace("\n", "\n  "))

    # --- 5) replicate disagreements (if biological_id used) ---
    if "biological_id" in combined.columns:
        has_bio = combined[combined["biological_id"].notna() &
                           combined["biological_id"].astype(str).str.strip().ne("")]
        if not has_bio.empty:
            groups = (has_bio.groupby("biological_id")["ST"]
                              .agg(lambda s: sorted(set(str(x) for x in s))))
            # Replicates with >1 unique ST (ignoring "-" = not called)
            disagree = groups[groups.apply(
                lambda lst: len([x for x in lst if x not in ("-", "nan")]) > 1
            )]
            rep_path = args.output / "replicates.tsv"
            disagree.apply(lambda lst: ",".join(lst)).rename("ST_values") \
                    .to_csv(rep_path, sep="\t")
            print(f"  wrote {rep_path}  ({len(disagree)} replicate group(s) with disagreement)")


if __name__ == "__main__":
    main()
