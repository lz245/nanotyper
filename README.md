# ONT-MLST: Nanopore Multi-Locus Sequence Typing

A portable, reproducible Snakemake workflow that takes Oxford Nanopore
`fastq_pass/` folders and produces MLST calls + an interactive HTML report.

**Target users:** scientists with no bioinformatics background.
**Platforms:** macOS (Intel + Apple Silicon) and Linux.
**Scheme:** *E. coli* Achtman (7 loci). Up to 96 barcodes per run.

---

## One-time setup

1. Install the pipeline:
   ```bash
   git clone https://github.com/<you>/ont-mlst-snakemake.git ~/ont-mlst-snakemake
   ~/ont-mlst-snakemake/install.sh
   ```
   `install.sh` checks/installs the two prerequisites (`mamba`/`conda` + `snakemake>=8`).
2. All other tools (medaka, BLAST, cutadapt, R) are installed automatically on the first run.

---

## Recommended project layout

Keep the pipeline, your raw sequencing data, and each analysis in **separate
directories**:

```
~/ont-mlst-snakemake/           ← the pipeline (code, versioned in git)
~/ont-mlst-data/                ← raw sequencing deliverables (read-only)
    run003_2025-11-01/
        fastq_pass/barcode01/ ...
    run004_2026-06-15/
        ...
~/ont-mlst-analyses/            ← one sub-folder per analysis
    2026-04_run003/
        samplesheet.csv         ← you edit this
        config.yaml             ← (optional) local overrides
        results/                ← pipeline writes outputs here
        logs/
    2026-06_run004/
        samplesheet.csv
        results/
```

Benefits: pipeline updates (`git pull`) don't touch your data or results; each
analysis is self-contained (zip it and send to a collaborator); multiple runs
don't step on each other's outputs.

---

## Daily workflow

What a typical run looks like end-to-end:

```bash
# 1. New sequencing run arrives — drop it in the data folder
cp -r ~/Downloads/run004_2026-06-15/ ~/ont-mlst-data/

# 2. Create an analysis folder for this run
mkdir -p ~/ont-mlst-analyses/2026-06_run004
cd       ~/ont-mlst-analyses/2026-06_run004

# 3. Write the samplesheet (use test/samplesheet.csv as a template)
cp ~/ont-mlst-analyses/test/samplesheet.csv .
# edit with your new sample IDs + barcodes + fastq_dir paths

# 4. Go
~/ont-mlst-snakemake/run.sh -n           # dry run — verify the plan
~/ont-mlst-snakemake/run.sh              # real run
open results/mlst_report.html
```

Outputs land in `./results/`:
- `mlst_summary.tsv` — one row per sample, ST + alleles + QC
- `mlst_summary.xlsx` — same data, colour-coded for Excel
- `mlst_report.html` — interactive report, open in any browser

**Tip — add a shell alias** so you don't retype the full path every time:

```bash
echo 'alias mlst="~/ont-mlst-snakemake/run.sh"' >> ~/.zshrc
source ~/.zshrc
# then just:  mlst          (or  mlst -n  for a dry run)
```

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
~/ont-mlst-analyses/2026-06_run004/
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

If you'd rather keep raw data elsewhere (e.g. `~/ont-mlst-data/run004/fastq_pass/`), either symlink it in:
```bash
ln -s ~/ont-mlst-data/run004/fastq_pass ./fastq_pass
```
or set a different template in a local `config.yaml`:
```yaml
paths:
  fastq_dir_template: "~/ont-mlst-data/{run_id}/fastq_pass/{barcode}"
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

## Overriding pipeline defaults

Drop a `config.yaml` in your analysis folder containing only the keys you want
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

---

## QC labels in the report

| label | meaning |
|---|---|
| **PASS** | All 7 loci known alleles, full coverage, ST found in PubMLST |
| **NEW_ST** | All 7 loci known alleles, but the 7-allele combination is novel |
| **NEW_ALLELE** | At least one locus has a hit <100% identity or not full length |
| **LOW_COVERAGE** | Any locus has 50–99× primer coverage (allele still called) |
| **FAIL** | Any locus has <50× coverage or no BLAST hit |

Priority order when multiple flags apply: FAIL > LOW_COVERAGE > NEW_ALLELE > NEW_ST > PASS.

Thresholds are tunable in `config.yaml` under `qc:`.

---

## Common commands

```bash
~/ont-mlst-snakemake/run.sh                  # full run
~/ont-mlst-snakemake/run.sh -n               # dry run
~/ont-mlst-snakemake/run.sh -j 4             # limit to 4 cores
~/ont-mlst-snakemake/run.sh --unlock         # recover from a crashed run
~/ont-mlst-snakemake/run.sh --forceall       # re-run everything from scratch
```

Tip: add an alias in your `~/.zshrc` or `~/.bashrc`:
```bash
alias mlst='~/ont-mlst-snakemake/run.sh'
```

---

## Troubleshooting

**`snakemake: command not found`** → run `~/ont-mlst-snakemake/install.sh`.

**First run is slow** → correct. Conda envs are being built. Subsequent runs reuse them.

**Sample labelled `FAIL`** → the report's "Samples needing attention" section
shows per-locus status dots and the exact reason (low coverage, no hit, etc.).

**Re-run just one sample** → delete `./results/<sample_id>/` and run `./run.sh`.

---

## Pipeline layout (for reference)

```
ont-mlst-snakemake/
├── Snakefile              ← pipeline definition
├── config.yaml            ← default paths, thresholds, MLST scheme
├── run.sh                 ← runner (call from your analysis folder)
├── install.sh             ← one-time setup
├── workflow/
│   ├── rules/             ← 7 Snakemake rule modules
│   ├── envs/              ← 5 conda env YAMLs (auto-installed)
│   ├── schemas/           ← JSON Schemas for samplesheet + config
│   └── scripts/           ← call_st.py, cutadapt_coverage.py, aggregate.py, report.Rmd
└── resources/
    └── databases/         ← PubMLST alleles, profiles, reference genome
```

---

## Credits

PubMLST *E. coli* Achtman scheme (Wirth et al. 2006).
Medaka (Oxford Nanopore Technologies).
BLAST+ (NCBI).
cutadapt (Martin 2011).
