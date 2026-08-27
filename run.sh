#!/usr/bin/env bash
# ------------------------------------------------------------------
# nanotyper runner — call this from one analysis folder.
#
# Usage:
#   cd ~/nanotyper-projects/<project>/analyses/<run>
#   ~/nanotyper/run.sh              # full run
#   ~/nanotyper/run.sh -n           # dry run
#   ~/nanotyper/run.sh -j 8         # 8 cores
#   ~/nanotyper/run.sh --unlock     # recover from a crash
#
# The current working directory must contain samplesheet.csv; outputs
# (results/, logs/) land there.
# ------------------------------------------------------------------
set -euo pipefail

# Where the pipeline lives (this script's directory).
PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Do NOT cd — we want to run in the user's current directory.
CWD="$(pwd)"

# ---- sanity checks ----
if ! command -v snakemake >/dev/null 2>&1; then
    echo "ERROR: 'snakemake' is not on PATH." >&2
    echo "  Run: ${PIPELINE_DIR}/install.sh" >&2
    exit 1
fi

if [[ ! -f "${CWD}/samplesheet.csv" ]]; then
    echo "ERROR: samplesheet.csv not found in ${CWD}" >&2
    echo "  This script must be run from an analysis folder that contains samplesheet.csv." >&2
    echo "  See ${PIPELINE_DIR}/README.md for the recommended layout." >&2
    exit 1
fi

# Conda environments are built once, in a shared location, and reused by
# every analysis folder. Override with NANOTYPER_CONDA_PREFIX if the pipeline
# directory is read-only (e.g. a shared install).
CONDA_PREFIX_DIR="${NANOTYPER_CONDA_PREFIX:-${PIPELINE_DIR}/.snakemake/conda}"

# Base args
ARGS=(
  --snakefile "${PIPELINE_DIR}/Snakefile"
  --use-conda
  --conda-prefix "${CONDA_PREFIX_DIR}"
  --cores all
  --rerun-incomplete
)

# If the analysis folder has its own config.yaml, layer it on top of the
# pipeline's default. (Without --configfile, Snakemake uses the bundled
# config.yaml at the pipeline root.)
if [[ -f "${CWD}/config.yaml" ]]; then
    ARGS+=(--configfile "${CWD}/config.yaml")
fi

echo "[run.sh] pipeline : ${PIPELINE_DIR}"
echo "[run.sh] workdir  : ${CWD}"
echo "[run.sh] conda    : ${CONDA_PREFIX_DIR}"
echo "[run.sh] launching: snakemake ${ARGS[*]} $*"

exec snakemake "${ARGS[@]}" "$@"
