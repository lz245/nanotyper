# nanotyper — Nanopore multilocus sequence typing

[![CI](https://github.com/lz245/nanotyper/actions/workflows/ci.yml/badge.svg)](https://github.com/lz245/nanotyper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A portable, reproducible Snakemake workflow that takes Oxford Nanopore
`fastq_pass/` folders of MLST amplicons and produces sequence-type (ST) calls,
per-locus QC, and an interactive HTML report.

**Target users:** microbiology labs with no bioinformatics support.
**Platforms:** macOS (Intel + Apple Silicon) and Linux.
**Scheme (v1.0):** *Escherichia coli* Achtman 7-locus MLST. Up to 96 barcodes per run.
**Supported chemistry:** R10.4.1 and later. Older flow cells (R9.4.1, R10.4) are
detected and flagged, but not supported — see "Basecalling model" below.
**Sibling tool:** [nano16s](https://github.com/lz245/nano16s) (full-length 16S profiling) from the same lab.

> **Relationship to the published method.** nanotyper is the successor to the
> ONT-MLST workflow described in Jia et al. (2024), *Poultry Science*
> 103:104067, [doi:10.1016/j.psj.2024.104067](https://doi.org/10.1016/j.psj.2024.104067).
> It is a re-implementation, not the code used in that paper: it uses current
> medaka models on all reads (the paper used medaka 1.3.2 on the first 4,000
> reads of R9.4 data), adds primer-coverage QC with explicit PASS/FAIL tiers,
> and supports 96-plex batch processing with cross-run aggregation.
>
> **Prior work with a similar name.** Two unrelated tools are called nanoMLST:
> Liou et al. 2020 (*Microbial Genomics*, MRSA, dual-barcode) and García-Pérez
> et al. 2025 (*MicrobiologyOpen*, ESKAPE+E, Krocus-based). nanotyper is not
> derived from either.

---

## One-time setup

1. Install the pipeline:
   ```bash
   git clone https://github.com/lz245/nanotyper.git ~/nanotyper
   ~/nanotyper/install.sh
   ```
   `install.sh` checks/installs the two prerequisites (`mamba`/`conda` + `snakemake>=8`).
2. All other tools (medaka, BLAST, cutadapt, R) are installed automatically on the first run.

---

## Try it in five minutes

The repository ships a four-barcode demo (three known STs and one deliberate
failure). After the one-time setup:

```bash
~/nanotyper/test/run_demo.sh
```

It runs the pipeline inside `test/demo/` and then checks the calls (ST602,
ST349, ST937 with every allele; barcode04 must FAIL). The first run also builds
the conda environments (~15 min); later runs take a few minutes.
Open `test/demo/results/mlst_report.html` to see what a report looks like.

---

## Recommended project layout

Keep the pipeline (code) separate from your projects (data + results). One
project folder holds everything for one study, so it can be moved, backed up,
or zipped and sent to a collaborator as a single self-contained record.

```
~/nanotyper/                              ← the pipeline (code, versioned in git)

~/nanotyper-projects/                     ← all your nanotyper studies
    2026-04_APEC-MLST-11-runs/            ← one folder per study
        data/                             ← raw MinKNOW output, read-only
            run003/fastq_pass/barcode01/ ...
            run003/samplesheet.csv        ← you write this (see below)
            run004/ ...
        analyses/                         ← created by batch_run.sh
            run003/samplesheet.csv
            run003/fastq_pass -> ../../data/run003/fastq_pass
            run003/results/               ← pipeline outputs
            run004/ ...
        combined/                         ← cross-run report + tables
        batch.log
    2026-09_next-study/
        data/  analyses/  combined/
```

Why this layout:
- Raw data is written once, never touched again → safe to keep read-only and back up
- Symlinks are relative, so the project folder survives being moved or archived
- Pipeline updates (`git pull` in `~/nanotyper/`) never touch data or results
- Rerun with different QC thresholds? Make a second analysis folder; data stays untouched

---

## Batch mode — the normal way to run

Put each sequencing run under `data/<run>/` with its `samplesheet.csv`, then:

```bash
~/nanotyper/batch_run.sh ~/nanotyper-projects/2026-04_APEC-MLST-11-runs
```

Behaviour:
- Runs sequentially (one run at a time; `-j 8` to give each run 8 cores, default 4). 11 runs × ~1 h ≈ overnight.
- **Resumable** — skips any run whose `results/mlst_report.html` already exists. Kill and restart safely.
- **Fail-fast** — if any run fails, the batch stops so you can fix that run and re-run to resume.
- Progress log at `<project>/batch.log` (append-only).

Aggregate-only (after the fact, without rerunning any pipelines):
```bash
~/nanotyper/batch_run.sh --aggregate ~/nanotyper-projects/2026-04_APEC-MLST-11-runs
```

Cross-run outputs land in `<project>/combined/`:

| file | contents |
|---|---|
| `combined_report.html` | self-contained cross-run report: status banner, per-run QC, top STs, ST × run heatmap, replicate disagreements, searchable sample table |
| `combined_summary.tsv` / `.xlsx` | all samples across all runs, one row each, with `run_folder` column |
| `st_distribution.tsv` | ST × run pivot — how often each ST appears per run |
| `qc_by_run.tsv` | QC-label × run pivot — success rate per run |
| `replicates.tsv` | (if `biological_id` used) replicates that disagree on ST |

## Single run

To run one analysis folder by hand (e.g. to re-run with different thresholds):

```bash
mkdir -p ~/nanotyper-projects/<project>/analyses/<run>
cd       ~/nanotyper-projects/<project>/analyses/<run>
ln -s ../../data/<run>/fastq_pass ./fastq_pass
cp    ../../data/<run>/samplesheet.csv ./samplesheet.csv

~/nanotyper/run.sh -n           # dry run — verify the plan
~/nanotyper/run.sh -j 4         # real run, 4 parallel cores
open results/mlst_report.html
```

Outputs in `./results/`:
- `mlst_summary.tsv` — one row per sample, ST + alleles + QC
- `mlst_summary.xlsx` — same data, colour-coded for Excel
- `mlst_report.html` — interactive report, open in any browser

**Tip — add a shell alias** so you don't retype the full path every time:

```bash
echo 'alias nanotyper="~/nanotyper/run.sh"' >> ~/.zshrc
source ~/.zshrc
# then just:  nanotyper          (or  nanotyper -n  for a dry run)
```

## Tools

Standalone utilities under `tools/`:

```bash
# Lint all samplesheets for duplicate sample_id (exit non-zero if problems):
~/nanotyper/tools/fix_samplesheet.py --check ~/nanotyper-projects/<project>/data/*/samplesheet.csv

# Auto-fix duplicates (suffix with _<barcode>, keep original in biological_id):
~/nanotyper/tools/fix_samplesheet.py --write /path/to/samplesheet.csv
```

`batch_run.sh` runs the check automatically as a pre-flight; use the write
mode only if you want to edit outside the batch flow.

---

## The samplesheet

One CSV, one row per sequencing event (run × barcode).

| column | required | description |
|---|---|---|
| `sample_id` | yes | **Unique** across the sheet. Becomes the result-folder name. Letters/digits/`_`/`.`/`-` only. |
| `run_id` | yes | Sequencing run label (e.g. `run003`) |
| `barcode` | yes | e.g. `barcode01` |
| `fastq_dir` | no | Path to the barcode's `.fastq.gz` folder. If omitted, auto-filled from `paths.fastq_dir_template` in `config.yaml` (default: `fastq_pass/{barcode}`). |
| `biological_id` | no | Underlying organism / source. Use to group replicates and cross-run controls. |
| `collection_date` | no | Free text; shown in the report |
| `sample_type` | no | Free text (e.g. `clinical`, `environmental`, `control`); shown in the report |

### The simplest samplesheet (recommended)

Put a `fastq_pass/` folder next to the samplesheet and omit `fastq_dir`:

```
data/run004/
├── samplesheet.csv
└── fastq_pass/
    ├── barcode01/
    ├── barcode02/
    └── ...
```

```csv
sample_id,run_id,barcode,sample_type
MS1451,run004,barcode01,clinical
MS1467,run004,barcode02,clinical
```

If the reads live somewhere else, either symlink them in or set a different
template in a local `config.yaml`:
```yaml
paths:
  fastq_dir_template: "/Volumes/lab-nas/minknow/{run_id}/fastq_pass/{barcode}"
```

### Handling replicates and controls

`sample_id` is the **technical** identifier (one row = one sequencing event,
never repeats). `biological_id` is the **organism** — use it to tie repeated
sequencings together.

```csv
sample_id,biological_id,run_id,barcode,sample_type
MS1451_rep1,MS1451,run003,barcode01,clinical
MS1451_rep2,MS1451,run004,barcode07,clinical
POS_CTRL_run003,POS_CTRL,run003,barcode96,control
POS_CTRL_run004,POS_CTRL,run004,barcode96,control
```
Two rows with the same `biological_id` are treated as replicates of the same
isolate.

### Validation

The pipeline validates the samplesheet before any tool runs. Typical failures
(missing columns, duplicate `sample_id`, bad path, empty fastq folder) produce
an error message that names the offending sample and the exact problem.

---

## Scheme packs

All organism-specific material lives in one directory per scheme under
`schemes/`; `config.yaml` selects it with `scheme: ecoli_achtman`.

```
schemes/ecoli_achtman/
├── scheme.yaml        ← organism, PubMLST database + scheme id, loci, amplicon sizes, QC defaults
├── reference.fasta    ← the 7 target genes (medaka reference)
├── primers.csv        ← forward/reverse primer per locus (primer-coverage QC)
└── pubmlst/           ← downloaded, not committed: alleles/<locus>.fasta, profiles.txt, database_info.txt
```

`install.sh` downloads the PubMLST snapshot once. To inspect or refresh it:

```bash
~/nanotyper/tools/fetch_pubmlst.py ecoli_achtman --check     # date and allele/ST counts
~/nanotyper/tools/fetch_pubmlst.py ecoli_achtman --update    # re-download (records the new date)
```

Every analysis writes `results/provenance.yaml` (pipeline version and commit,
scheme, PubMLST snapshot date and counts, medaka model, pinned tool versions),
and the report footer shows the scheme and snapshot date. Refreshing the
snapshot can change `NEW_ST` / `NEW_ALLELE` labels because PubMLST keeps adding
records — see `docs/decisions/0009-database-snapshot-policy.md`.

Adding another organism means adding one scheme pack directory (see
`CONTRIBUTING.md`); nothing else in the pipeline changes.

## Overriding pipeline defaults

Drop a `config.yaml` in the analysis folder containing only the keys you want
to change. Example:
```yaml
qc:
  coverage_good: 75         # keep ST calls down to 75× primer coverage
  coverage_warn: 30
medaka:
  model: r1041_e82_400bps_hac_v5.0.0   # HAC instead of SUP
```
Unspecified keys fall back to the pipeline defaults (see
[`config.yaml`](config.yaml) at the pipeline root).

**Medaka model:** the default targets R10.4.1 flow cells (`r1041_*`). Pick the
`r1041_*` model that matches your basecalling mode (fast / hac / sup). Older
chemistries are out of scope (see "Basecalling model").

---

## QC labels in the report

| label | meaning |
|---|---|
| **PASS** | All 7 loci known alleles, full coverage, ST found in PubMLST |
| **NEW_ST** | All 7 loci known alleles, but the 7-allele combination is novel |
| **NEW_ALLELE** | At least one locus has a hit <100% identity or not full length |
| **LOW_COVERAGE** | Any locus has 20–99× primer coverage (allele still called) |
| **FAIL** | Any locus has <20× coverage or no BLAST hit |

Priority order when multiple flags apply: FAIL > LOW_COVERAGE > NEW_ALLELE > NEW_ST > PASS.

Thresholds are tunable in `config.yaml` under `qc:`, and the defaults are
calibrated rather than assumed: on 480 R10.4.1/SUP-v5 samples, locus calls that
miss a known allele run at ~32 % below 20×, ~20 % from 20–100×, and ~5 % above
200× (`docs/qc-calibration.md`, `docs/decisions/0012-qc-thresholds.md`).

### Locus balance

The report also flags **primer imbalance**. If a locus takes a small share of a
sample's on-target reads (<3 % by default, `qc.min_locus_share_pct`), that locus
caps the sample's QC no matter how deep the run is. In this lab's *E. coli* data
*mdh* sits at ~2.5 % of reads, so ~3,900 reads per barcode are needed for *mdh*
alone to reach 100×. The fix is the primer ratio at the bench (Jia et al. 2024,
Fig. 2), not a lower threshold — so the report tells you the required read count
instead of hiding the problem.

### Basecalling model

Each sample's `basecall_model_version_id` is read from the FASTQ headers, recorded
in the summary and `provenance.yaml`, and compared with the medaka model in use.
A mismatch is flagged, because reads basecalled on one chemistry and polished with a
model for another keep motif-specific errors that BLAST reports as novel alleles.

**nanotyper targets R10.4.1 and later only.** Legacy R9.4.1 and R10.4 data are
deliberately out of scope: medaka 2.x no longer ships those model families, Oxford
Nanopore has retired the chemistries, and carrying a second polishing environment for
them would add a maintenance burden with no future users. In the lab dataset behind
`docs/qc-calibration.md`, legacy runs produced imperfect BLAST matches at 12–21 % of
locus calls even at ≥200× depth, against 5 % on R10.4.1 — so their allele calls should
be treated as provisional. If you must analyse such data, re-basecall it with a current
model first.

To re-derive all of this on your own project:

```bash
~/nanotyper/tools/qc_calibration.py ~/nanotyper-projects/<project> --out qc-calibration.md
```

---

## Common commands

```bash
~/nanotyper/run.sh                  # full run (inside an analysis folder)
~/nanotyper/run.sh -n               # dry run
~/nanotyper/run.sh -j 4             # limit to 4 cores
~/nanotyper/run.sh --unlock         # recover from a crashed run
~/nanotyper/run.sh --forceall       # re-run everything from scratch
```

---

## Troubleshooting

**`snakemake: command not found`** → run `~/nanotyper/install.sh`.

**First run is slow** → correct. Conda envs are being built. Subsequent runs reuse them.

**Sample labelled `FAIL`** → the report's "Samples needing attention" section
shows per-locus status dots and the exact reason (low coverage, no hit, etc.).

**Re-run just one sample** → delete `./results/<sample_id>/` and run `~/nanotyper/run.sh`.

---

## Pipeline layout (for reference)

```
nanotyper/
├── Snakefile              ← pipeline definition
├── config.yaml            ← defaults: scheme selection, thresholds, medaka model
├── run.sh                 ← single-run runner (call from an analysis folder)
├── batch_run.sh           ← project-level batch runner + cross-run aggregation
├── install.sh             ← one-time setup
├── schemes/
│   └── ecoli_achtman/     ← scheme pack (see "Scheme packs")
├── tools/                 ← fetch_pubmlst.py, fix_samplesheet.py, qc_calibration.py, make_demo.py
├── workflow/
│   ├── rules/             ← Snakemake rule modules (one per step)
│   ├── envs/              ← 5 conda env YAMLs (auto-installed, shared across analyses)
│   ├── schemas/           ← JSON Schemas for samplesheet, config, scheme pack
│   └── scripts/           ← call_st.py, cutadapt_coverage.py, aggregate.py, batch_aggregate.py, provenance.py, report.Rmd
└── docs/decisions/        ← design decision records
```

---

## Validation

[`docs/validation.md`](docs/validation.md) records how the calls were checked: 480
isolates across five R10.4.1 runs, compared one-to-one against the lab's earlier
pipeline on the same reads — **100 % allele agreement on `known` calls (2,994/2,994)
and 100 % ST agreement (287/287)**, with the limitations stated (legacy chemistry
excluded, one shallow run, metadata errors the replicate check surfaced, and a residual
5.2 % of `NEW_ALLELE` calls awaiting confirmation).

## Citing

See [`CITATION.cff`](CITATION.cff). Please also cite the underlying tools:
PubMLST *E. coli* Achtman scheme (Wirth et al. 2006; Jolley et al. 2018),
medaka (Oxford Nanopore Technologies), BLAST+ (NCBI), cutadapt (Martin 2011),
Snakemake (Mölder et al. 2021).

## License

MIT — see [`LICENSE`](LICENSE).
