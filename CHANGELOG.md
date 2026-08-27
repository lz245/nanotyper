# Changelog

All notable changes to nanotyper are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow semantic versioning.

## [Unreleased]

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
