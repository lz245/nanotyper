# ONT-MLST: Nanopore Multi-Locus Sequence Typing

A portable, reproducible Snakemake workflow that takes Oxford Nanopore
`fastq_pass/` folders and produces MLST calls + an interactive HTML report.

**Target users:** scientists with no bioinformatics background.
**Platforms:** macOS (Intel + Apple Silicon) and Linux.
**Scheme:** *E. coli* Achtman (7 loci). Up to 96 barcodes per run.

---

## What you need

1. A Mac or Linux computer.
2. **mamba** (or conda). If you don't have it, install
   [Miniforge](https://github.com/conda-forge/miniforge) — free, one-click.
3. **snakemake** (install once, in your base env):
   ```bash
   mamba install -n base -c conda-forge -c bioconda 'snakemake>=8'
   ```

All other tools (medaka, BLAST, cutadapt, R) are installed automatically on the first run.

---

## Quick start

```bash
# 1. Edit samplesheet.csv — list one row per barcode.
open samplesheet.csv          # macOS; opens in Excel/Numbers

# 2. Run the pipeline.
./run.sh
```

That's it. First run installs tool environments (~10 min, one-time). Subsequent runs are fast.

Outputs land in `results/`:
- `results/mlst_summary.tsv` — one row per sample, ST + alleles + QC
- `results/mlst_report.html` — interactive report, open in any browser

---

## The samplesheet

One CSV, one row per sample. Columns:

| column | required | description |
|---|---|---|
| `sample_id` | yes | Must be unique across the whole sheet |
| `run_id` | yes | Sequencing run label |
| `barcode` | yes | e.g. `barcode01` |
| `fastq_dir` | yes | Absolute path to the barcode's folder of `.fastq.gz` files |
| `collection_date` | no | Free text; shown in the report |
| `sample_type` | no | Free text; shown in the report |

Example:
```csv
sample_id,run_id,barcode,fastq_dir,collection_date,sample_type
MS1451,run003,barcode01,/data/run003/fastq_pass/barcode01,2025-11-01,clinical
```

---

## QC labels in the report

| label | meaning |
|---|---|
| **PASS** | All 7 loci known alleles, full coverage, ST found in PubMLST |
| **NEW_ST** | All 7 loci known alleles, but the 7-allele combination is novel |
| **NEW_ALLELE** | At least one locus has a hit <100% identity or not full length |
| **LOW_COVERAGE** | Any locus has 50–99× primer coverage (allele still called) |
| **FAIL** | Any locus has <50× coverage or no BLAST hit |

Thresholds are tunable in `config.yaml` under `qc:`.

---

## Common commands

```bash
./run.sh                  # full run
./run.sh -n               # dry run, show what would happen
./run.sh -j 4             # limit to 4 cores
./run.sh --unlock         # recover from a crashed run
./run.sh --forceall       # re-run everything from scratch
```

---

## Troubleshooting

**"snakemake: command not found"** → install it per *What you need* above.

**First run is slow** → correct. Conda envs are being built. Subsequent runs reuse them.

**A sample has `qc_label=FAIL`** → the report shows why (no BLAST hit, low coverage, etc.).

**I want to re-run just one sample** → delete its `results/<sample_id>/` folder and run `./run.sh`.

---

## Directory layout

```
ont-mlst-snakemake/
├── Snakefile              ← pipeline definition
├── config.yaml            ← paths, thresholds, MLST scheme
├── samplesheet.csv        ← YOU edit this
├── run.sh                 ← one-command wrapper
├── workflow/
│   ├── rules/             ← 7 Snakemake rule modules
│   ├── envs/              ← 5 conda env YAMLs (auto-installed)
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
