# 0010 — Demo dataset and continuous integration

**Date**: 2026-08-27

**Decided**:
- The repo ships a demo dataset (`test/demo/`, ~11 MB): three *E. coli* barcodes
  subsampled to 7,000 reads each with long-established STs (602, 349, 937) plus one
  428-read barcode that must FAIL. Subsampling is deterministic (`tools/make_demo.py`,
  `manifest.tsv`, seed 42) so the set is regenerable from the lab's raw data.
- The demo runs at the **default QC thresholds**. `test/check_demo.py` asserts the exact
  STs, all seven alleles, the QC labels, ≥100× both-primer coverage at every locus of the
  PASS samples, and the presence/content of `provenance.yaml` and the report footer.
- Unit tests (`pytest test/`) cover the MLST-calling and QC-tier logic, the samplesheet
  linter, and the fetch-script parser. `call_st.py` was refactored into pure functions
  with `main()` as the only Snakemake-aware entry point; behaviour unchanged.
- GitHub Actions: `unit` (ubuntu + macOS, py3.10/3.12), `lint` (ruff, shellcheck,
  `snakemake --lint`), `demo` (ubuntu: real `install.sh` incl. PubMLST download, cached
  conda envs, full pipeline on the demo, `check_demo.py`). Weekly cron catches bioconda drift.

**Why 7,000 reads**: with these primers the weakest locus (*mdh*) is 1.3–2.2 % of reads in
every test barcode, so ~7,000 reads are needed for *mdh* to clear `coverage_good: 100`.
The alternative — 3,000 reads with lowered demo thresholds — was rejected by the PI so the
demo exercises the shipped defaults. (This *mdh* share is also why runs 008/010 are
LOW_COVERAGE-heavy; carried to the validation work.)

**Why exact assertions**: MLST is deterministic for a pinned snapshot, and the demo STs'
allele numbers are stable across PubMLST releases. A structural smoke test would not
catch a wrong allele call.

**What CI does not prove**: macOS execution of medaka/R (only unit tests run on macOS);
performance; behaviour on R9.4 data. CI itself is unverified until the first push.
