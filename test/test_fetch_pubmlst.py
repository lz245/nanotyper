"""Offline tests for tools/fetch_pubmlst.py (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fetch_pubmlst  # noqa: E402

INFO = """# PubMLST snapshot for nanotyper scheme pack: ecoli_achtman
# Downloaded: 2025-11-04 00:04:58 UTC
# Source: https://rest.pubmlst.org/db/pubmlst_escherichia_seqdef/schemes/1
# Scheme ID: 1

Allele Sequences:
  adk: 1914 alleles
  recA: 1246 alleles

Sequence Type Profiles:
  Total STs: 16242
"""


def test_check_reports_snapshot(tmp_path, capsys):
    (tmp_path / "database_info.txt").write_text(INFO)
    assert fetch_pubmlst.check(tmp_path) == 0
    out = capsys.readouterr().out
    assert "2025-11-04" in out and "adk: 1914 alleles" in out and "Total STs: 16242" in out


def test_check_missing_snapshot(tmp_path, capsys):
    assert fetch_pubmlst.check(tmp_path) == 1
    assert "no snapshot" in capsys.readouterr().out


def test_count_fasta(tmp_path):
    f = tmp_path / "x.fasta"
    f.write_text(">a_1\nACGT\n>a_2\nACGT\n")
    assert fetch_pubmlst.count_fasta(f) == 2


def test_real_scheme_pack_has_pubmlst_block():
    import yaml
    meta = yaml.safe_load((Path(__file__).resolve().parents[1] / "schemes" / "ecoli_achtman" / "scheme.yaml").read_text())
    assert meta["pubmlst"] == {"database": "pubmlst_escherichia_seqdef", "scheme_id": 1}
    assert meta["loci"] == ["adk", "fumC", "gyrB", "icd", "mdh", "purA", "recA"]
