#!/usr/bin/env bash
# ------------------------------------------------------------------
# Run nanotyper on the bundled demo dataset and check the calls.
#
# USAGE
#   ~/nanotyper/test/run_demo.sh            # run + check (first run builds conda envs)
#   ~/nanotyper/test/run_demo.sh -n         # dry run only
#   ~/nanotyper/test/run_demo.sh -j 8       # more cores
#
# Runs inside test/demo/ (a normal analysis folder); results/ is gitignored.
# ------------------------------------------------------------------
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(dirname "$HERE")"
cd "$HERE/demo"

DRY=0
for a in "$@"; do [[ "$a" == "-n" ]] && DRY=1; done

"$PIPELINE_DIR/run.sh" "$@"

if [[ $DRY -eq 0 ]]; then
    python3 "$HERE/check_demo.py" "$HERE/demo/results"
fi
