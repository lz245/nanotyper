"""Unit tests for the locus-balance and basecall-model helpers in workflow/scripts/aggregate.py."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow" / "scripts"))
import aggregate  # noqa: E402

LOCI = ["adk", "fumC", "gyrB", "icd", "mdh", "purA", "recA"]


def test_locus_shares_sum_to_100():
    cov = {"adk": 4176, "fumC": 1599, "gyrB": 945, "icd": 817, "mdh": 233, "purA": 4453, "recA": 1124}
    sh = aggregate.locus_shares(cov)
    assert round(sum(sh.values()), 6) == 100.0
    assert sh["mdh"] < sh["adk"]


def test_locus_shares_zero_reads():
    assert aggregate.locus_shares({l: 0 for l in LOCI}) == {l: 0.0 for l in LOCI}


def test_balance_note_flags_starved_locus_weakest_first():
    sh = {"adk": 40.0, "purA": 55.0, "mdh": 2.0, "icd": 3.0}
    note = aggregate.balance_note(sh, 5)
    assert note.startswith("low_share:mdh=2.0%"), note
    assert "icd=3.0%" in note


def test_balance_note_empty_when_balanced():
    assert aggregate.balance_note({l: 100 / 7 for l in LOCI}, 3) == ""


def test_balance_note_boundary_is_exclusive():
    assert aggregate.balance_note({"mdh": 3.0}, 3) == ""
    assert aggregate.balance_note({"mdh": 2.99}, 3) != ""


@pytest.mark.parametrize("model,family", [
    ("dna_r10.4.1_e8.2_400bps_sup@v5.0.0", "r1041"),
    ("r1041_e82_400bps_sup_v5.0.0", "r1041"),
    ("2021-05-17_dna_r9.4.1_minion_96_29d8704b", "r941"),
    ("2021-09-03_dna_r10.4_minion_promethion_384", "r104"),
    ("", "unknown"),
    ("unknown", "unknown"),
])
def test_model_family(model, family):
    assert aggregate.model_family(model) == family


def test_model_mismatch_flags_r9_polished_with_r1041():
    note = aggregate.model_mismatch("2021-05-17_dna_r9.4.1_minion_96", "r1041_e82_400bps_sup_v5.0.0")
    assert note.startswith("basecall_model_mismatch:")


def test_model_mismatch_silent_when_families_agree():
    assert aggregate.model_mismatch("dna_r10.4.1_e8.2_400bps_sup@v5.0.0", "r1041_e82_400bps_sup_v5.0.0") == ""


def test_model_mismatch_silent_when_unknown():
    assert aggregate.model_mismatch("unknown", "r1041_e82_400bps_sup_v5.0.0") == ""
    assert aggregate.model_mismatch("", "r1041_e82_400bps_sup_v5.0.0") == ""


def test_read_basecall_models(tmp_path):
    for sample, text in [("S1", "dna_r10.4.1_e8.2_400bps_sup@v5.0.0\n"), ("S2", "\n")]:
        d = tmp_path / sample / "medaka"
        d.mkdir(parents=True)
        (d / "basecall_model.txt").write_text(text)
    got = aggregate.read_basecall_models([
        tmp_path / "S1" / "medaka" / "basecall_model.txt",
        tmp_path / "S2" / "medaka" / "basecall_model.txt",
        tmp_path / "S3" / "medaka" / "basecall_model.txt",   # missing file
    ])
    assert got["S1"].startswith("dna_r10.4.1")
    assert got["S2"] == "unknown"
    assert got["S3"] == "unknown"


def test_aggregate_module_imports_without_snakemake():
    """The module must be importable outside Snakemake (main() holds all state)."""
    assert hasattr(aggregate, "main")
