"""Unit tests for the MLST calling and QC-tier logic in workflow/scripts/call_st.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow" / "scripts"))
import call_st  # noqa: E402

LOCI = ["adk", "fumC", "gyrB", "icd", "mdh", "purA", "recA"]


def blast_row(sseqid, pident=100.0, length=536, slen=536, bitscore=990.0):
    return "\t".join(map(str, ["q", sseqid, pident, length, 0, 0, 1, length, 1, length, 0.0, bitscore, 600, slen]))


@pytest.mark.parametrize("sseqid,expected", [
    ("adk_42", "42"), ("adk-42", "42"), ("fumC_1234", "1234"), ("weird7x", "7"), ("noid", "noid"),
])
def test_parse_allele_id(sseqid, expected):
    assert call_st.parse_allele_id(sseqid) == expected


def test_call_locus_known(tmp_path):
    p = tmp_path / "s_adk.tsv"
    p.write_text(blast_row("adk_20") + "\n")
    assert call_st.call_locus(p, 100.0, True) == ("20", 100.0, 536, "known")


def test_call_locus_best_hit_by_bitscore(tmp_path):
    p = tmp_path / "s_adk.tsv"
    p.write_text(blast_row("adk_5", bitscore=500) + "\n" + blast_row("adk_20", bitscore=990) + "\n")
    assert call_st.call_locus(p, 100.0, True)[0] == "20"


def test_call_locus_new_allele_on_identity(tmp_path):
    p = tmp_path / "s_adk.tsv"
    p.write_text(blast_row("adk_20", pident=99.81) + "\n")
    assert call_st.call_locus(p, 100.0, True)[3] == "new_allele"


def test_call_locus_new_allele_on_partial_length(tmp_path):
    p = tmp_path / "s_adk.tsv"
    p.write_text(blast_row("adk_20", length=500, slen=536) + "\n")
    assert call_st.call_locus(p, 100.0, True)[3] == "new_allele"
    assert call_st.call_locus(p, 100.0, False)[3] == "known"  # full length not required


def test_call_locus_no_hit(tmp_path):
    empty = tmp_path / "s_adk.tsv"
    empty.write_text("")
    assert call_st.call_locus(empty, 100.0, True) == ("-", 0.0, 0, "no_hit")
    assert call_st.call_locus(tmp_path / "missing.tsv", 100.0, True)[3] == "no_hit"


def test_lookup_st(tmp_path):
    prof = tmp_path / "profiles.txt"
    prof.write_text("ST\tadk\tfumC\tgyrB\ticd\tmdh\tpurA\trecA\tclonal_complex\n"
                    "602\t6\t4\t12\t1\t20\t13\t7\t\n"
                    "10\t10\t11\t4\t8\t8\t8\t2\tST10 Cplx\n")
    assert call_st.lookup_st(prof, dict(zip(LOCI, ["6", "4", "12", "1", "20", "13", "7"])), LOCI) == "602"
    assert call_st.lookup_st(prof, dict(zip(LOCI, ["6", "4", "12", "1", "20", "13", "99"])), LOCI) == "new_ST"


def _known():
    return {l: "known" for l in LOCI}


def _cov(v=500):
    return {l: float(v) for l in LOCI}


def test_qc_pass():
    assert call_st.assign_qc(_known(), _cov(), LOCI, 50, 100, "602") == ("PASS", "")


def test_qc_new_st():
    assert call_st.assign_qc(_known(), _cov(), LOCI, 50, 100, "new_ST")[0] == "NEW_ST"


def test_qc_new_allele_beats_new_st():
    flags = _known()
    flags["mdh"] = "new_allele"
    label, notes = call_st.assign_qc(flags, _cov(), LOCI, 50, 100, "-")
    assert label == "NEW_ALLELE" and notes == "new_allele:mdh"


def test_qc_low_coverage_beats_new_allele():
    flags = _known()
    flags["mdh"] = "new_allele"
    cov = _cov()
    cov["icd"] = 75.0
    label, notes = call_st.assign_qc(flags, cov, LOCI, 50, 100, "-")
    assert label == "LOW_COVERAGE" and notes == "mid_cov:icd"


def test_qc_fail_on_low_cov_beats_everything():
    cov = _cov()
    cov["mdh"] = 49.0
    label, notes = call_st.assign_qc(_known(), cov, LOCI, 50, 100, "602")
    assert label == "FAIL" and notes == "low_cov:mdh"


def test_qc_fail_on_missing_locus_lists_it():
    flags = _known()
    flags["fumC"] = "no_hit"
    label, notes = call_st.assign_qc(flags, _cov(), LOCI, 50, 100, "-")
    assert label == "FAIL" and "missing_locus:fumC" in notes


def test_qc_thresholds_are_inclusive_at_good_and_warn():
    cov = _cov()
    cov["adk"] = 100.0
    assert call_st.assign_qc(_known(), cov, LOCI, 50, 100, "602")[0] == "PASS"
    cov["adk"] = 50.0
    assert call_st.assign_qc(_known(), cov, LOCI, 50, 100, "602")[0] == "LOW_COVERAGE"


def test_call_sample_end_to_end(tmp_path):
    prof = tmp_path / "profiles.txt"
    prof.write_text("ST\tadk\tfumC\tgyrB\ticd\tmdh\tpurA\trecA\tclonal_complex\n602\t6\t4\t12\t1\t20\t13\t7\t\n")
    cov = tmp_path / "cov.tsv"
    cov.write_text("locus\tfwd\trev\tboth\n" + "".join(f"{l}\t900\t900\t800\n" for l in LOCI))
    alleles = dict(zip(LOCI, ["6", "4", "12", "1", "20", "13", "7"]))
    tsvs = []
    for l in LOCI:
        p = tmp_path / f"S1_{l}.tsv"
        p.write_text(blast_row(f"{l}_{alleles[l]}") + "\n")
        tsvs.append(str(p))
    row = call_st.call_sample("S1", tsvs, cov, prof, LOCI, 100.0, True, 100, 50)
    assert row["ST"] == "602" and row["qc_label"] == "PASS"
    assert [row[l] for l in LOCI] == list(alleles.values())
    assert row["mdh_coverage"] == 800 and row["mdh_flag"] == "known"
