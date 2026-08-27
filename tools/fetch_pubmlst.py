#!/usr/bin/env python3
"""
Download (or refresh) the PubMLST allele sequences and ST profiles for a
nanotyper scheme pack.

USAGE
    tools/fetch_pubmlst.py <scheme>              # download if pubmlst/ is missing
    tools/fetch_pubmlst.py <scheme> --update     # re-download and overwrite
    tools/fetch_pubmlst.py <scheme> --check      # report snapshot date/age, no network

    <scheme> is a directory name under schemes/ (e.g. ecoli_achtman) whose
    scheme.yaml has a `pubmlst:` block with `database` and `scheme_id`.

What it writes into schemes/<scheme>/pubmlst/:
    alleles/<locus>.fasta      one FASTA per locus (BLAST indexes are built by the pipeline)
    profiles.txt               ST profile table (tab-separated, as served by PubMLST)
    scheme_info.json           the scheme record returned by the REST API
    database_info.txt          download timestamp, source URLs, allele and ST counts

Notes
    - Uses only the Python standard library (no requests) so it runs in the
      base environment created by install.sh.
    - PubMLST's unauthenticated REST API serves a lagged snapshot: at the time
      of writing, records submitted after 2024-12-31 require authentication.
      The exact restriction message (if any) is recorded in database_info.txt.
      Full-dataset access via OAuth is not implemented.
    - PubMLST asks users to cite Jolley et al. 2018, Wellcome Open Res 3:124.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

REST = "https://rest.pubmlst.org"
HERE = Path(__file__).resolve().parent.parent  # pipeline root


def get(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": "nanotyper-fetch_pubmlst"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: could not fetch {url}\n  {e}\n  (no internet? PubMLST down?)")
    return data if binary else data.decode()


def count_fasta(path: Path) -> int:
    with open(path) as fh:
        return sum(1 for line in fh if line.startswith(">"))


def check(pub: Path) -> int:
    info = pub / "database_info.txt"
    if not info.exists():
        print(f"no snapshot: {pub} (run without --check to download)")
        return 1
    text = info.read_text()
    m = re.search(r"^# Downloaded: (\S+)", text, re.M)
    if m:
        try:
            dl = datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dl).days
            print(f"snapshot downloaded {m.group(1)} ({age} days ago): {pub}")
        except ValueError:
            print(f"snapshot downloaded {m.group(1)}: {pub}")
    else:
        print(f"snapshot present (no download date recorded): {pub}")
    for line in text.splitlines():
        if re.match(r"^\s+(\w+): \d+ alleles|^\s+Total STs", line):
            print("  " + line.strip())
    return 0


def fetch(scheme_dir: Path, update: bool) -> int:
    meta = yaml.safe_load((scheme_dir / "scheme.yaml").read_text())
    try:
        db = meta["pubmlst"]["database"]
        sid = int(meta["pubmlst"]["scheme_id"])
    except (KeyError, TypeError, ValueError):
        sys.exit(f"ERROR: {scheme_dir / 'scheme.yaml'} has no usable pubmlst.database / pubmlst.scheme_id")
    loci_expected = list(meta["loci"])

    pub = scheme_dir / "pubmlst"
    if pub.exists() and not update:
        print(f"snapshot already present: {pub}\n  use --update to refresh, --check to inspect")
        return 0
    (pub / "alleles").mkdir(parents=True, exist_ok=True)

    scheme_url = f"{REST}/db/{db}/schemes/{sid}"
    print(f"scheme   : {scheme_url}")
    scheme = json.loads(get(scheme_url))
    (pub / "scheme_info.json").write_text(json.dumps(scheme, indent=2))
    restriction = scheme.get("message", "")
    if restriction:
        print(f"NOTE     : {restriction}")

    loci_urls = {u.rstrip("/").split("/")[-1]: u for u in scheme["loci"]}
    missing = [l for l in loci_expected if l not in loci_urls]
    if missing:
        sys.exit(f"ERROR: scheme {sid} in {db} does not contain loci {missing}; scheme.yaml loci = {loci_expected}")

    counts = {}
    for locus in loci_expected:
        url = f"{loci_urls[locus]}/alleles_fasta"
        out = pub / "alleles" / f"{locus}.fasta"
        out.write_bytes(get(url, binary=True))
        counts[locus] = count_fasta(out)
        print(f"alleles  : {locus:6s} {counts[locus]:6d}  <- {url}")
        # remove stale BLAST indexes so the pipeline rebuilds them
        for idx in pub.glob(f"alleles/{locus}.fasta.n*"):
            idx.unlink()

    prof_url = scheme["profiles_csv"]
    prof = pub / "profiles.txt"
    prof.write_bytes(get(prof_url, binary=True))
    n_st = max(0, sum(1 for _ in open(prof)) - 1)
    print(f"profiles : {n_st} STs  <- {prof_url}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# PubMLST snapshot for nanotyper scheme pack: {scheme_dir.name}",
        f"# Downloaded: {now} UTC",
        f"# Source: {scheme_url}",
        f"# Scheme ID: {sid}",
        f"# Database: {db}",
        f"# Restriction: {restriction or 'none reported'}",
        "",
        f"Scheme: {scheme.get('description', '')}",
        f"Loci: {len(loci_expected)} ({', '.join(loci_expected)})",
        "",
        "Allele Sequences:",
        *[f"  {l}: {counts[l]} alleles" for l in loci_expected],
        "",
        "Sequence Type Profiles:",
        f"  Total STs: {n_st}",
        "",
        "Citation: Jolley KA, Bray JE, Maiden MCJ. 2018. Wellcome Open Res 3:124. doi:10.12688/wellcomeopenres.14826.1",
        "",
    ]
    (pub / "database_info.txt").write_text("\n".join(lines))
    print(f"written  : {pub / 'database_info.txt'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scheme", help="scheme pack name under schemes/ (e.g. ecoli_achtman)")
    ap.add_argument("--update", action="store_true", help="re-download even if a snapshot exists")
    ap.add_argument("--check", action="store_true", help="report the existing snapshot; no network")
    ap.add_argument("--schemes-dir", type=Path, default=HERE / "schemes", help=argparse.SUPPRESS)
    a = ap.parse_args()

    scheme_dir = a.schemes_dir / a.scheme
    if not (scheme_dir / "scheme.yaml").exists():
        sys.exit(f"ERROR: no scheme pack at {scheme_dir} (expected scheme.yaml)")
    if a.check:
        return check(scheme_dir / "pubmlst")
    return fetch(scheme_dir, a.update)


if __name__ == "__main__":
    sys.exit(main())
