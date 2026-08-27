# 0009 — PubMLST database snapshot policy

**Date**: 2026-08-26

**Decided**:
- PubMLST alleles and profiles are **not committed**. Each scheme pack carries a
  `pubmlst/` directory that `tools/fetch_pubmlst.py <scheme>` downloads from the
  PubMLST REST API, together with a `database_info.txt` recording the download
  timestamp, source URLs, allele and ST counts, and any access restriction reported
  by the server.
- The lab's working snapshot is the **2025-11-04 download** (adk 1914, fumC 2602,
  gyrB 1635, icd 2074, mdh 1640, purA 1487, recA 1246 alleles; 16,242 STs), copied
  unchanged into `schemes/ecoli_achtman/pubmlst/` on 2026-08-26. All validation runs
  were called against it. Refreshing is an explicit `--update` action, recorded in
  the changelog and in a new decision record when it changes any validation result.
- Every analysis writes `results/provenance.yaml` naming the scheme and the snapshot
  date, and the HTML report footer shows them, so any ST call can be traced to a
  database version.

**Why**: PubMLST only ever adds alleles and STs, so a newer snapshot can silently turn
`NEW_ST` / `NEW_ALLELE` labels into known ones; reproducibility of a published result
requires pinning the snapshot. Vendoring the files in git would freeze them and
obscure PubMLST as the citable source (Jolley et al. 2018).

**Known limitation**: unauthenticated REST access is restricted to records submitted
on or before 2024-12-31 (server message, observed 2025-11-04 and 2026-08-26). The
fetch script records the message; OAuth access to the full dataset is not implemented.

**Rejected**: committing the snapshot (stale, large, not citable); fetching fresh on
every install without recording the date (irreproducible).
