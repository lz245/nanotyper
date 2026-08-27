#!/usr/bin/env bash
# ------------------------------------------------------------------
# nanotyper batch runner — analyse every sequencing run in a project
# folder, then build a cross-run report.
#
# Usage:
#   batch_run.sh <project_dir>                 # run everything, then aggregate
#   batch_run.sh -j 8 <project_dir>            # cores per run (default 4)
#   batch_run.sh --aggregate <project_dir>     # re-aggregate only, no pipeline runs
#
# Project layout (input you create):
#   <project_dir>/data/<run>/fastq_pass/barcodeNN/*.fastq.gz
#   <project_dir>/data/<run>/samplesheet.csv
#
# Project layout (produced):
#   <project_dir>/analyses/<run>/samplesheet.csv           (copied from data/)
#   <project_dir>/analyses/<run>/fastq_pass -> ../../data/<run>/fastq_pass   (relative symlink)
#   <project_dir>/analyses/<run>/results/...               (pipeline outputs)
#   <project_dir>/combined/                                (cross-run aggregates)
#   <project_dir>/batch.log                                (append-only progress log)
#
# Behaviour:
#   - Sequential: one run at a time (each uses -j cores).
#   - Idempotent: skips runs whose results/mlst_report.html already exists.
#   - Fail-fast: stops on first failure so you can debug, then re-run to resume.
#   - Relative symlinks: the whole project folder can be moved or zipped intact.
# ------------------------------------------------------------------
set -euo pipefail

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say()  { printf "\033[1;36m[batch]\033[0m %s\n" "$*"; }
ok()   { printf "\033[1;32m[batch]\033[0m ✓ %s\n" "$*"; }
err()  { printf "\033[1;31m[batch]\033[0m ✗ %s\n" "$*" >&2; }
usage() { sed -n '2,27p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' >&2; exit 1; }

# ---- parse args ----
AGGREGATE_ONLY=0
JOBS=4
PROJECT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --aggregate|aggregate) AGGREGATE_ONLY=1; shift ;;
        -j|--jobs) JOBS="${2:?-j needs a number}"; shift 2 ;;
        -h|--help) usage ;;
        -*) err "unknown option: $1"; usage ;;
        *) [[ -z "$PROJECT" ]] || { err "unexpected extra argument: $1"; usage; }
           PROJECT="$1"; shift ;;
    esac
done
[[ -n "$PROJECT" ]] || { err "project folder required"; usage; }
[[ -d "$PROJECT" ]] || { err "project folder not found: $PROJECT"; exit 1; }
PROJECT="$(cd "$PROJECT" && pwd)"

DATA_ROOT="$PROJECT/data"
ANALYSIS_ROOT="$PROJECT/analyses"
COMBINED="$PROJECT/combined"
BATCH_LOG="$PROJECT/batch.log"
log() { printf "[%s] %s\n" "$(date +'%F %T')" "$*" | tee -a "$BATCH_LOG"; }

# ======================================================================
# RUN MODE: iterate data/<run>/ → one pipeline per run
# ======================================================================
if [[ $AGGREGATE_ONLY -eq 0 ]]; then
    [[ -d "$DATA_ROOT" ]] || { err "No data/ folder in $PROJECT — expected data/<run>/fastq_pass/..."; exit 1; }
    mkdir -p "$ANALYSIS_ROOT"

    say "pipeline : $PIPELINE_DIR"
    say "project  : $PROJECT"
    say "cores/run: $JOBS"
    say "log      : $BATCH_LOG"
    log "=== batch start ==="

    runs=()
    for d in "$DATA_ROOT"/*/; do
        [[ -d "$d" ]] || continue
        runs+=("${d%/}")
    done
    if [[ ${#runs[@]} -eq 0 ]]; then
        err "No run folders under $DATA_ROOT — expected data/<run>/fastq_pass/..."
        exit 1
    fi
    say "Found ${#runs[@]} run(s):"
    for r in "${runs[@]}"; do echo "    $(basename "$r")"; done
    echo

    # Pre-flight samplesheet lint: duplicate sample_id is the #1 way a batch
    # fails. Scan everything up front so problems are fixed in one pass.
    say "Linting samplesheets..."
    sheets=()
    for r in "${runs[@]}"; do
        [[ -f "$r/samplesheet.csv" ]] && sheets+=("$r/samplesheet.csv")
    done
    if [[ ${#sheets[@]} -gt 0 ]] && ! python3 "$PIPELINE_DIR/tools/fix_samplesheet.py" --check "${sheets[@]}"; then
        err "Duplicate sample_id (or similar) found above."
        err "Auto-fix (backup originals as .bak):"
        err "    python3 $PIPELINE_DIR/tools/fix_samplesheet.py --write <samplesheet.csv>"
        err "...then re-run batch_run.sh."
        exit 1
    fi
    ok "All samplesheets pass lint."

    total_start=$(date +%s)
    n_done=0; n_skip=0; n_fail=0

    for run_dir in "${runs[@]}"; do
        run=$(basename "$run_dir")
        analysis="$ANALYSIS_ROOT/$run"

        if [[ -f "$analysis/results/mlst_report.html" ]]; then
            ok "$run — already analysed, skipping"
            log "skip $run"
            n_skip=$((n_skip + 1))
            continue
        fi
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

        # Set up the analysis folder: relative symlink to the raw data so the
        # project folder stays self-contained when moved or archived.
        mkdir -p "$analysis"
        if [[ ! -e "$analysis/fastq_pass" ]]; then
            ln -s "../../data/$run/fastq_pass" "$analysis/fastq_pass"
        fi
        if [[ ! -f "$analysis/samplesheet.csv" ]]; then
            cp "$run_dir/samplesheet.csv" "$analysis/samplesheet.csv"
        fi

        say "Running $run ..."
        run_start=$(date +%s)
        log "start $run"
        if (cd "$analysis" && "$PIPELINE_DIR/run.sh" -j "$JOBS" > run.log 2>&1); then
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
[[ -d "$ANALYSIS_ROOT" ]] || { err "No analyses/ folder in $PROJECT — nothing to aggregate"; exit 1; }
mkdir -p "$COMBINED"

summaries=()
for d in "$ANALYSIS_ROOT"/*/; do
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
