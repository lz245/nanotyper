"""Unit tests for tools/fix_samplesheet.py (samplesheet lint / auto-fix)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fix_samplesheet  # noqa: E402


def test_inspect_clean():
    df = pd.DataFrame({"sample_id": ["A", "B"], "run_id": ["r1", "r1"], "barcode": ["barcode01", "barcode02"]})
    assert fix_samplesheet.inspect(df) == {}


def test_inspect_duplicate_sample_id_and_run_barcode():
    df = pd.DataFrame({"sample_id": ["A", "A"], "run_id": ["r1", "r1"], "barcode": ["barcode01", "barcode01"]})
    issues = fix_samplesheet.inspect(df)
    assert issues["duplicate_sample_id"] == ["A"]
    assert issues["duplicate_run_barcode"] == ["(run_id=r1, barcode=barcode01)"]


def test_inspect_missing_column():
    assert fix_samplesheet.inspect(pd.DataFrame({"x": [1]})) == {"missing_column": "sample_id"}


def test_fix_disambiguates_and_keeps_biological_id():
    df = pd.DataFrame({"sample_id": ["A", "A", "B"], "run_id": ["r1"] * 3, "barcode": ["barcode01", "barcode02", "barcode03"]})
    out = fix_samplesheet.fix(df)
    assert list(out["sample_id"]) == ["A_barcode01", "A_barcode02", "B"]
    assert list(out["biological_id"])[:2] == ["A", "A"]
    assert fix_samplesheet.inspect(out) == {}
