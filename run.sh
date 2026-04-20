#!/usr/bin/env bash
# ------------------------------------------------------------------
# ONT-MLST one-command runner
#
# Usage:
#   ./run.sh                # run the full pipeline with defaults
#   ./run.sh -n             # dry run (show what would happen, no execution)
#   ./run.sh -j 8           # use 8 cores
#   ./run.sh --unlock       # unlock a stale working directory
#   ./run.sh <any snakemake args...>
#
# Requirements (install once):
#   - mamba or conda (https://github.com/conda-forge/miniforge)
#   - snakemake >=8 in the base env:
#       mamba install -n base -c conda-forge -c bioconda snakemake
# ------------------------------------------------------------------
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# Default: run with conda envs and all cores
DEFAULT_ARGS=(--use-conda --cores all --rerun-incomplete)

if ! command -v snakemake >/dev/null 2>&1; then
    cat >&2 <<EOF
ERROR: 'snakemake' is not on PATH.

Install it once with mamba (recommended) or conda:
    mamba install -n base -c conda-forge -c bioconda 'snakemake>=8'

Then re-run: ./run.sh
EOF
    exit 1
fi

# Quick sanity check: samplesheet exists
if [[ ! -f samplesheet.csv ]]; then
    echo "ERROR: samplesheet.csv not found in $HERE" >&2
    echo "  Edit the file to list your samples, then re-run." >&2
    exit 1
fi

echo "[run.sh] launching: snakemake ${DEFAULT_ARGS[*]} $*"
exec snakemake "${DEFAULT_ARGS[@]}" "$@"
