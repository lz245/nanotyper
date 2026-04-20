# ==================================================================
# ONT-MLST Snakemake workflow
#   Nanopore amplicon -> medaka consensus -> BLAST -> MLST call
#   + parallel cutadapt primer-coverage QC
# ==================================================================

import pandas as pd
import subprocess
from pathlib import Path

configfile: "config.yaml"

# ---- pipeline version + git commit (for provenance in the report) ----
def _read_version() -> str:
    p = Path("VERSION")
    return p.read_text().strip() if p.exists() else "dev"

def _read_git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "no-git"

PIPELINE_VERSION = _read_version()
PIPELINE_COMMIT  = _read_git_sha()

# ---- load samplesheet ----
samples = pd.read_csv(config["paths"]["samplesheet"]).set_index("sample_id", drop=False)
SAMPLES = samples.index.tolist()

# Enforce unique sample IDs
if len(SAMPLES) != len(set(SAMPLES)):
    raise ValueError("Duplicate sample_id values found in samplesheet.csv")

LOCI = config["mlst"]["loci"]
RESULTS = config["paths"]["results_dir"]

# ---- helper: fastq_dir for a given sample ----
def fastq_dir(wildcards):
    return samples.loc[wildcards.sample, "fastq_dir"]

# ---- top-level target ----
rule all:
    input:
        f"{RESULTS}/mlst_summary.tsv",
        f"{RESULTS}/mlst_summary.xlsx",
        f"{RESULTS}/mlst_report.html"

# ---- rule modules ----
include: "workflow/rules/references.smk"
include: "workflow/rules/medaka.smk"
include: "workflow/rules/blast.smk"
include: "workflow/rules/call_st.smk"
include: "workflow/rules/cutadapt.smk"
include: "workflow/rules/aggregate.smk"
include: "workflow/rules/report.smk"
