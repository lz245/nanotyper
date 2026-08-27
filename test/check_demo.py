#!/usr/bin/env python3
"""
Check that a nanotyper demo run produced the expected calls.

Unlike a structural smoke test, this asserts the *specific* STs and alleles,
because MLST is deterministic for a pinned PubMLST snapshot and the demo STs
(602, 349, 937) are long-established — their allele numbers never change.

USAGE
    python3 test/check_demo.py [results_dir]        # default: test/demo/results

Exits 0 if everything matches, 1 otherwise.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LOCI = ["adk", "fumC", "gyrB", "icd", "mdh", "purA", "recA"]

GREEN, RED, RESET = "\033[32m", "\033[31m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = RESET = ""
problems: list[str] = []


def ok(msg):
    print(f"  {GREEN}ok{RESET}    {msg}")


def fail(msg):
    print(f"  {RED}FAIL{RESET}  {msg}")
    problems.append(msg)


def main() -> int:
    results = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "demo" / "results"
    expected = {r["sample_id"]: r for r in csv.DictReader(open(HERE / "demo" / "expected.tsv"), delimiter="\t")}

    print(f"nanotyper demo check: {results}")
    for name in ("mlst_summary.tsv", "mlst_long.tsv", "mlst_summary.xlsx", "mlst_report.html", "provenance.yaml"):
        (ok if (results / name).exists() else fail)(f"{name} present")
    if problems:
        return finish()

    got = {r["sample_id"]: r for r in csv.DictReader(open(results / "mlst_summary.tsv"), delimiter="\t")}
    missing = sorted(set(expected) - set(got))
    (fail if missing else ok)(f"all {len(expected)} demo samples in summary" + (f" — missing {missing}" if missing else ""))

    for sid, exp in expected.items():
        r = got.get(sid)
        if not r:
            continue
        if r["qc_label"] != exp["qc_label"]:
            fail(f"{sid}: qc_label {r['qc_label']} != expected {exp['qc_label']} (notes: {r.get('qc_notes', '')})")
        else:
            ok(f"{sid}: qc_label {r['qc_label']}")
        if exp["qc_label"] == "FAIL":
            continue  # alleles/ST are not asserted for the deliberate failure sample
        if r["ST"] != exp["ST"]:
            fail(f"{sid}: ST {r['ST']} != expected {exp['ST']}")
        else:
            ok(f"{sid}: ST {r['ST']}")
        bad = [f"{l}={r[l]}(exp {exp[l]})" for l in LOCI if r[l] != exp[l]]
        (fail if bad else ok)(f"{sid}: alleles " + (", ".join(bad) if bad else "/".join(r[l] for l in LOCI)))
        low = [f"{l}={r[l + '_coverage']}" for l in LOCI if int(float(r[l + "_coverage"])) < 100]
        (fail if low else ok)(f"{sid}: every locus >= 100x both-primer coverage" + (f" — {low}" if low else ""))

    prov = yaml.safe_load((results / "provenance.yaml").read_text())
    (ok if prov.get("scheme", {}).get("name") == "ecoli_achtman" else fail)("provenance.yaml scheme = ecoli_achtman")
    (ok if prov.get("pubmlst_snapshot", {}).get("downloaded") else fail)("provenance.yaml records the PubMLST snapshot date")
    (ok if prov.get("tool_versions", {}).get("medaka") else fail)("provenance.yaml records tool versions")

    # pandoc re-wraps text, so normalise whitespace before matching phrases
    html = " ".join((results / "mlst_report.html").read_text(errors="replace").split())
    (ok if "ecoli_achtman" in html and "PubMLST snapshot" in html else fail)("report footer names the scheme and snapshot")
    return finish()


def finish() -> int:
    if problems:
        print(f"\n{RED}{len(problems)} problem(s){RESET}")
        return 1
    print(f"\n{GREEN}all checks passed{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
