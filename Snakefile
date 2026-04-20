# ==================================================================
# ONT-MLST Snakemake workflow
#   Nanopore amplicon -> medaka consensus -> BLAST -> MLST call
#   + parallel cutadapt primer-coverage QC
# ==================================================================

import pandas as pd
import subprocess
from pathlib import Path

from snakemake.utils import validate
from snakemake.exceptions import WorkflowError

configfile: "config.yaml"

# ---- schema validation: catch bad inputs BEFORE any tools run ----
validate(config, "workflow/schemas/config.schema.yaml")

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

# ---- load + validate samplesheet ----
_ss_path = config["paths"]["samplesheet"]
if not Path(_ss_path).exists():
    raise WorkflowError(
        f"Samplesheet not found: {_ss_path}\n"
        f"  Edit config.yaml -> paths.samplesheet, or create {_ss_path}."
    )

samples = pd.read_csv(_ss_path)

# Row-level structure (required columns, types, sample_id pattern)
validate(samples, "workflow/schemas/samplesheet.schema.yaml")

def _validate_samplesheet(df: pd.DataFrame) -> None:
    errs = []

    # 1) unique sample_id
    dup_ids = df["sample_id"][df["sample_id"].duplicated(keep=False)].unique().tolist()
    if dup_ids:
        errs.append(f"duplicate sample_id values: {sorted(dup_ids)}")

    # 2) <= 96 samples (Nanopore native barcoding limit)
    if len(df) > 96:
        errs.append(
            f"samplesheet has {len(df)} rows; >96 per run is unusual for "
            f"Nanopore native barcoding. Split into multiple runs."
        )

    # 3) every fastq_dir must exist, be a directory, and contain .fastq.gz
    for _, row in df.iterrows():
        sid = row["sample_id"]
        fq  = Path(str(row["fastq_dir"]))
        if not fq.exists():
            errs.append(f"{sid}: fastq_dir does not exist -> {fq}")
            continue
        if not fq.is_dir():
            errs.append(f"{sid}: fastq_dir is not a directory -> {fq}")
            continue
        if not list(fq.glob("*.fastq.gz")):
            errs.append(f"{sid}: no *.fastq.gz files found in {fq}")

    # 4) (run_id, barcode) should be unique — catches copy-paste mistakes
    key_dups = (
        df.groupby(["run_id", "barcode"])
          .size().reset_index(name="n")
          .query("n > 1")
    )
    if not key_dups.empty:
        for _, r in key_dups.iterrows():
            errs.append(f"(run_id={r.run_id}, barcode={r.barcode}) appears {r.n} times")

    if errs:
        bullets = "\n  - ".join(errs)
        raise WorkflowError(
            f"Samplesheet validation failed ({len(errs)} problem(s)):\n  - {bullets}\n"
            f"Edit {_ss_path} and re-run."
        )

_validate_samplesheet(samples)

samples = samples.set_index("sample_id", drop=False)
SAMPLES = samples.index.tolist()

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
