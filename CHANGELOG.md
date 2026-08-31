# Changelog

All notable changes to nanotyper are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semantic versioning.

## [Unreleased]

### Added
- Zenodo DOI badge and `doi:` / `identifiers:` in `CITATION.cff` (concept DOI 10.5281/zenodo.22131409,
  v1.0.0 DOI 10.5281/zenodo.22131410).
- `docs/tested-on.md` — environments where the shipped demo has been run end to end,
  with the wall-clock time and whether the conda environments were already built (#14).

### Fixed
- Use the supported JSON Schema 2020-12 identifier to avoid validator warnings on fresh installs.

## [1.0.0] — 2026-08-27

First full release. The pipeline, demo, tests and CI shipped in 0.9.0; what makes this 1.0
is that the QC thresholds are now calibrated against data rather than assumed, the supported
chemistry is stated, and the calls are validated and documented.

### Changed
- **QC threshold `coverage_warn` 50 → 20** (`coverage_good` unchanged at 100): a locus at
  20–99× is now `LOW_COVERAGE` with its tentative ST shown, not `FAIL`. Calibrated on 480
  R10.4.1/SUP-v5 samples — see `docs/qc-calibration.md` and `docs/decisions/0012-qc-thresholds.md`.
  **Labels from earlier runs change; re-run before quoting PASS rates.**
- Every coverage threshold shown in the HTML report now follows `config.yaml` instead of
  being hard-coded.

### Added
- Locus-balance QC: `<locus>_share_pct`, `locus_balance_note` (threshold
  `qc.min_locus_share_pct`, default 3 %), `share_pct` in the long table, and a report panel
  that converts the weakest locus's share into the reads per barcode needed to reach `coverage_good`.
- `docs/validation.md` — agreement with the lab's earlier pipeline over 480 isolates on five
  R10.4.1 runs (100 % on `known` allele calls, 100 % on STs, with the all-call figure and every
  limitation stated), the before/after effect of the calibrated thresholds, and how to reproduce it.
- **Supported chemistry stated explicitly: R10.4.1 and later.** Legacy R9.4.1 / R10.4 data are
  detected and flagged as provisional rather than supported (see `docs/decisions/0012-qc-thresholds.md`).
- Basecalling-model detection: `basecall_model_version_id` from the FASTQ headers is recorded
  per sample (`basecall_model`), checked against the medaka model (`model_note`), reported, and
  written to `provenance.yaml`.
- `tools/qc_calibration.py` — regenerates `docs/qc-calibration.md` (locus share, call quality vs
  depth overall and by chemistry, recurrent mismatch positions, candidate threshold rules) from
  any finished project folder.

## [0.9.0] — 2026-08-27 — public pre-release

First public version, published as a **release candidate**: the pipeline, demo,
tests and CI are complete; the validation write-up, the medaka R9/R10 policy,
and the per-locus QC-threshold decision (issues #1–#5) are scheduled for 1.0.0.

### Changed
- Renamed the project from `ont-mlst-snakemake` to **nanotyper** (see `docs/decisions/0001-name-nanotyper.md`).
- `batch_run.sh` now takes a single project folder (`<project>/data/<run>/` in, `<project>/analyses/<run>/` and `<project>/combined/` out), creates relative symlinks, and accepts `-j <cores>`.
- README rewritten for the project-folder layout; documents the relationship to Jia et al. 2024 and the two unrelated nanoMLST tools.
- `install.sh` no longer expects a `samplesheet.csv` inside the pipeline directory.

### Added
- **Scheme packs**: all organism-specific material now lives in `schemes/<name>/`
  (`scheme.yaml`, `reference.fasta`, `primers.csv`, downloaded `pubmlst/`); `config.yaml`
  selects `scheme: ecoli_achtman`. `resources/databases` symlink removed — a fresh clone
  can run after one `tools/fetch_pubmlst.py ecoli_achtman`.
- `tools/fetch_pubmlst.py`: downloads/refreshes a scheme's PubMLST alleles and profiles and
  writes `database_info.txt` with date, counts, and server access restriction.
- `results/provenance.yaml` in every analysis (pipeline version + commit, scheme, PubMLST
  snapshot date and counts, medaka model, pinned tool versions); report footer shows scheme
  and snapshot date.
- Shared conda environment location (`<pipeline>/.snakemake/conda`, override with
  `NANOTYPER_CONDA_PREFIX`) so environments are built once, not per analysis folder.
- Demo dataset (`test/demo/`, 4 barcodes, 11 MB) with `test/run_demo.sh` and `test/check_demo.py`
  asserting exact STs/alleles/QC labels; `tools/make_demo.py` regenerates it deterministically.
- Unit tests (`pytest test/`) for MLST calling, QC tiers, samplesheet lint, fetch-script parsing;
  `call_st.py` refactored into importable pure functions (no behaviour change).
- GitHub Actions CI (`unit`, `lint`, `demo` jobs; weekly cron), `ruff.toml`, `.pre-commit-config.yaml`.
- `LICENSE` (MIT), `CITATION.cff`, `CONTRIBUTING.md`, repo-level `CLAUDE.md`, and `docs/decisions/` design records.
- `.gitignore` rules for session backups, raw reads, and derived BLAST/minimap2 index files.

## [0.1.0] — 2026-04-19

Initial Snakemake implementation (as `ont-mlst-snakemake`).

### Added
- Per-sample workflow: merge fastq → medaka consensus against the 7 concatenated
  MLST genes → BLAST per locus against PubMLST alleles → ST lookup → QC tiers
  (PASS / NEW_ST / NEW_ALLELE / LOW_COVERAGE / FAIL).
- Parallel cutadapt primer-coverage QC per locus.
- Aggregation to `mlst_summary.tsv` / `.xlsx` and an interactive R Markdown HTML report
  carrying pipeline version and git commit.
- JSON-schema validation of `config.yaml` and the samplesheet before any tool runs;
  `fastq_dir` optional via `paths.fastq_dir_template`; `biological_id` column for replicates.
- Pipeline runnable from any analysis directory (`run.sh`), with local `config.yaml` overrides.
- `batch_run.sh` for many runs plus `batch_aggregate.py` (cross-run summary, ST × run and
  QC × run pivots, replicate disagreements, combined HTML report).
- `tools/fix_samplesheet.py` samplesheet linter / auto-fixer.

### Fixed
- Samplesheet-vs-calls merge failing silently when all `sample_id` values are digits.
