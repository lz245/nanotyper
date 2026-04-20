#!/usr/bin/env bash
# ------------------------------------------------------------------
# ONT-MLST one-time setup
#
# Checks/installs the two prerequisites:
#   1. mamba or conda  (package manager — we do NOT auto-install this;
#                       we tell you how if missing)
#   2. snakemake >=8   (in your base conda env — we DO auto-install)
#
# After this finishes:
#   1. Edit samplesheet.csv
#   2. ./run.sh
# ------------------------------------------------------------------
set -euo pipefail

say()  { printf "\033[1;36m[install.sh]\033[0m %s\n"     "$*"; }
ok()   { printf "\033[1;32m[install.sh]\033[0m ✓ %s\n"   "$*"; }
warn() { printf "\033[1;33m[install.sh]\033[0m ⚠ %s\n"   "$*"; }
err()  { printf "\033[1;31m[install.sh]\033[0m ✗ %s\n"   "$*" >&2; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# ---------------- 1) OS + arch ----------------
OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in
  Darwin|Linux) ok "OS: $OS ($ARCH)" ;;
  *) err "Unsupported OS: $OS. Use macOS or Linux."; exit 1 ;;
esac

# ---------------- 2) mamba / conda ----------------
HAVE_MAMBA=0
HAVE_CONDA=0
command -v mamba >/dev/null 2>&1 && HAVE_MAMBA=1
command -v conda >/dev/null 2>&1 && HAVE_CONDA=1

if [[ $HAVE_MAMBA -eq 0 && $HAVE_CONDA -eq 0 ]]; then
  err "Neither 'mamba' nor 'conda' is on PATH."
  cat >&2 <<EOF

You need a package manager. We recommend Miniforge (free, open-source):

  macOS (Apple Silicon):
    curl -L -o /tmp/miniforge.sh \\
      https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh
    bash /tmp/miniforge.sh -b -p \$HOME/miniforge3
    \$HOME/miniforge3/bin/conda init "\$(basename \$SHELL)"

  macOS (Intel):
    curl -L -o /tmp/miniforge.sh \\
      https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh
    bash /tmp/miniforge.sh -b -p \$HOME/miniforge3
    \$HOME/miniforge3/bin/conda init "\$(basename \$SHELL)"

  Linux (x86_64):
    curl -L -o /tmp/miniforge.sh \\
      https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
    bash /tmp/miniforge.sh -b -p \$HOME/miniforge3
    \$HOME/miniforge3/bin/conda init "\$(basename \$SHELL)"

Then restart your shell and re-run ./install.sh
EOF
  exit 1
fi

if [[ $HAVE_MAMBA -eq 1 ]]; then
  MV="$(mamba --version 2>&1 | head -1 || true)"
  ok "Found mamba ($MV)"
  PKGMGR=(mamba)
else
  CV="$(conda --version 2>&1 || true)"
  ok "Found conda ($CV)"
  warn "mamba is much faster than conda. Consider:  conda install -n base -c conda-forge mamba"
  PKGMGR=(conda)
fi

# ---------------- 3) snakemake in base env ----------------
if command -v snakemake >/dev/null 2>&1; then
  SMV="$(snakemake --version 2>/dev/null || echo unknown)"
  # Compare major version
  SM_MAJOR="${SMV%%.*}"
  if [[ "$SM_MAJOR" =~ ^[0-9]+$ ]] && (( SM_MAJOR >= 8 )); then
    ok "snakemake already installed (version $SMV)"
  else
    warn "snakemake $SMV is older than 8.x; upgrading..."
    "${PKGMGR[@]}" install -y -n base -c conda-forge -c bioconda 'snakemake>=8' pandas openpyxl plotly
    ok "snakemake upgraded to $(snakemake --version 2>/dev/null)"
  fi
else
  say "Installing snakemake into base env (this is a one-time install)..."
  "${PKGMGR[@]}" install -y -n base -c conda-forge -c bioconda 'snakemake>=8' pandas openpyxl plotly
  # Re-check
  if ! command -v snakemake >/dev/null 2>&1; then
    err "snakemake install appears to have failed."
    err "Try manually:  ${PKGMGR[*]} install -n base -c conda-forge -c bioconda 'snakemake>=8' pandas openpyxl plotly"
    exit 1
  fi
  ok "snakemake installed ($(snakemake --version 2>/dev/null))"
fi

# ---------------- 4) Sanity: databases + samplesheet ----------------
[[ -d resources/databases ]] \
  && ok "resources/databases/ present" \
  || warn "resources/databases/ not found — set this up before running (see README.md)"

[[ -f samplesheet.csv ]] \
  && ok "samplesheet.csv present" \
  || warn "samplesheet.csv missing — copy the example and edit with your samples"

# ---------------- 5) Done ----------------
cat <<EOF

────────────────────────────────────────────────────────────────
  ✓ Setup complete.
────────────────────────────────────────────────────────────────

Next steps:
  1. Edit samplesheet.csv        — one row per barcode
  2. ./run.sh -n                 — dry run (shows the plan, no execution)
  3. ./run.sh                    — real run
                                   (first run auto-installs tool envs, ~15 min)

Outputs land in results/:
  - results/mlst_summary.tsv     — wide, one row per sample
  - results/mlst_summary.xlsx    — same data, colour-coded for Excel
  - results/mlst_report.html     — interactive report (open in any browser)

For help:  cat README.md
EOF
