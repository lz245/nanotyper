#!/usr/bin/env bash
# ------------------------------------------------------------------
# Batch-run the ONT-MLST pipeline across every run in a data folder.
#
# Usage:
#   batch_run.sh                          # all defaults
#   batch_run.sh <data_root>              # custom data root
#   batch_run.sh <data_root> <analysis_root>
#   batch_run.sh --aggregate [<analysis_root>]   # re-aggregate only
#
# Defaults:
#   <data_root>     = ~/ont-mlst-data
#   <analysis_root> = ~/ont-mlst-analyses
#
# Layout expected:
#   <data_root>/<run>/fastq_pass/barcodeNN/   (input raw data)
#   <data_root>/<run>/samplesheet.csv         (symlink/copy target)
# Layout produced:
#   <analysis_root>/<run>/fastq_pass -> data    (symlink)
#   <analysis_root>/<run>/samplesheet.csv       (copy)
#   <analysis_root>/<run>/results/...           (outputs)
#   <analysis_root>/combined/                   (cross-run aggregates)
#   <analysis_root>/batch.log                   (append-only progress log)
#
# Behaviour:
#   - Sequential: one run at a time (each uses all cores).
#   - Idempotent: skips runs whose results/mlst_report.html already exists.
#   - Fail-fast: stops on first failure so you can debug, then re-run to resume.
# ------------------------------------------------------------------
set -euo pipefail

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say()  { printf "\033[1;36m[batch]\033[0m %s\n" "$*"; }
ok()   { printf "\033[1;32m[batch]\033[0m ✓ %s\n" "$*"; }
err()  { printf "\033[1;31m[batch]\033[0m ✗ %s\n" "$*" >&2; }

# ---- parse args ----
AGGREGATE_ONLY=0
if [[ "${1:-}" == "--aggregate" || "${1:-}" == "aggregate" ]]; then
    AGGREGATE_ONLY=1
    shift
fi

DATA_ROOT="${1:-$HOME/ont-mlst-data}"
ANALYSIS_ROOT="${2:-$HOME/ont-mlst-analyses}"

if [[ $AGGREGATE_ONLY -eq 1 ]]; then
    # In aggregate-only mode, ANALYSIS_ROOT is the first positional arg
    ANALYSIS_ROOT="${1:-$HOME/ont-mlst-analyses}"
fi

mkdir -p "$ANALYSIS_ROOT"
BATCH_LOG="$ANALYSIS_ROOT/batch.log"
log() { printf "[%s] %s\n" "$(date +'%F %T')" "$*" | tee -a "$BATCH_LOG"; }

# ======================================================================
# RUN MODE: iterate data_root/*/ → one pipeline per run
# ======================================================================
if [[ $AGGREGATE_ONLY -eq 0 ]]; then
    [[ -d "$DATA_ROOT" ]] || { err "Data root not found: $DATA_ROOT"; exit 1; }

    say "pipeline      : $PIPELINE_DIR"
    say "data root     : $DATA_ROOT"
    say "analysis root : $ANALYSIS_ROOT"
    say "log           : $BATCH_LOG"
    log "=== batch start ==="

    runs=()
    for d in "$DATA_ROOT"/*/; do
        [[ -d "$d" ]] || continue
        runs+=("$d")
    done

    if [[ ${#runs[@]} -eq 0 ]]; then
        err "No subfolders under $DATA_ROOT — expected <data_root>/<run>/fastq_pass/..."
        exit 1
    fi

    say "Found ${#runs[@]} run(s):"
    for r in "${runs[@]}"; do echo "    $(basename "$r")"; done
    echo

    total_start=$(date +%s)
    n_done=0
    n_skip=0
    n_fail=0

    for run_dir in "${runs[@]}"; do
        run_dir="${run_dir%/}"
        run=$(basename "$run_dir")
        analysis="$ANALYSIS_ROOT/$run"

        # Skip if already fully analysed
        if [[ -f "$analysis/results/mlst_report.html" ]]; then
            ok "$run — already analysed, skipping"
            log "skip $run"
            n_skip=$((n_skip + 1))
            continue
        fi

        # Pre-flight
        if [[ ! -d "$run_dir/fastq_pass" ]]; then
            err "$run — no $run_dir/fastq_pass, skipping"
            log "fail $run (no fastq_pass)"
            n_fail=$((n_fail + 1))
            continue
        fi
        if [[ ! -f "$run_dir/samplesheet.csv" ]]; then
            err "$run — no $run_dir/samplesheet.csv, skipping"
            log "fail $run (no samplesheet.csv)"
            n_fail=$((n_fail + 1))
            continue
        fi

        # Set up analysis folder
        mkdir -p "$analysis"
        if [[ ! -e "$analysis/fastq_pass" ]]; then
            ln -s "$run_dir/fastq_pass" "$analysis/fastq_pass"
        fi
        if [[ ! -f "$analysis/samplesheet.csv" ]]; then
            cp "$run_dir/samplesheet.csv" "$analysis/samplesheet.csv"
        fi

        # Run pipeline
        say "Running $run ..."
        run_start=$(date +%s)
        log "start $run"
        if (cd "$analysis" && "$PIPELINE_DIR/run.sh" -j 4 > run.log 2>&1); then
            dur=$(( $(date +%s) - run_start ))
            ok "$run — completed in ${dur}s"
            log "done $run (${dur}s)"
            n_done=$((n_done + 1))
        else
            err "$run — FAILED. See $analysis/run.log"
            log "fail $run"
            err "Batch halted. Fix this run and re-run batch_run.sh to resume."
            exit 1
        fi
    done

    total_dur=$(( $(date +%s) - total_start ))
    log "=== batch end ==="
    say ""
    ok "Batch done. completed=$n_done skipped=$n_skip failed=$n_fail  total=${total_dur}s"
fi

# ======================================================================
# AGGREGATE: concatenate per-run summaries into a cross-run view
# ======================================================================
say "Aggregating per-run summaries..."
COMBINED="$ANALYSIS_ROOT/combined"
mkdir -p "$COMBINED"

summaries=()
for d in "$ANALYSIS_ROOT"/*/; do
    [[ "$(basename "$d")" == "combined" ]] && continue
    [[ -f "$d/results/mlst_summary.tsv" ]] && summaries+=("$d/results/mlst_summary.tsv")
done

if [[ ${#summaries[@]} -eq 0 ]]; then
    err "No mlst_summary.tsv files found under $ANALYSIS_ROOT"
    exit 1
fi

say "Found ${#summaries[@]} per-run summaries"

AGG="$PIPELINE_DIR/workflow/scripts/batch_aggregate.py"
if ! python3 -c "import pandas" 2>/dev/null; then
    err "python3 + pandas required for aggregation."
    err "Install once:  mamba install -n base -c conda-forge pandas openpyxl"
    exit 1
fi

python3 "$AGG" \
    --analysis-root "$ANALYSIS_ROOT" \
    --output "$COMBINED" \
    "${summaries[@]}"

ok "Combined outputs in $COMBINED/"
