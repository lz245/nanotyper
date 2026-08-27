# nanotyper — instructions for AI coding assistants

This file is read automatically by Claude Code (and similar tools) working in
this repository. It applies to every contributor's sessions.

## What this project is

A Snakemake workflow for MLST calling from Oxford Nanopore amplicon reads.
v1.0 ships the *E. coli* Achtman scheme; the design is organism-agnostic via
scheme packs. Successor to Jia et al. 2024 (*Poultry Science* 103:104067) — a
re-implementation, not that paper's code. Two unrelated tools are named
nanoMLST; never describe nanotyper as derived from them.

## Hard rules

- **Never commit data**: `results/`, fastq, PubMLST downloads, BLAST/minimap2
  indexes. If a task seems to need it, stop and ask.
- **Never change a scientific threshold or database source without a decision
  record** in `docs/decisions/NNNN-<slug>.md` (Decided / Why / Rejected). This
  includes `qc.coverage_*`, `blast.min_identity`, `blast.require_full_length`,
  `cutadapt.error_rate`, the medaka model default, and reference sequences.
- **Organism-specific material lives only in a scheme pack** (`schemes/<organism>_<scheme>/`).
  Do not hard-code *E. coli* loci, primers, or PubMLST IDs anywhere else.
- **Pipeline logic changes need a passing dry run** (`run.sh -n`) and the demo
  dataset test before a PR is opened.
- **Update `CHANGELOG.md` `[Unreleased]`** with every user-visible change.

## Conventions

- Shell scripts: `set -euo pipefail`; USAGE block at top with the exact
  invocation; full tool names in filenames (`minimap2`, not `mm2`).
- Python: `ruff format` + `ruff check`; scripts under `workflow/scripts/` are
  Snakemake `script:` targets and read `snakemake.input/output/params`.
  Keep the logic in pure functions and touch `snakemake` only in `main()`, so
  `test/` can import them. **Never start a Snakemake script with
  `from __future__ import ...`** — Snakemake prepends a preamble, so the import
  is no longer the first statement and the rule fails with SyntaxError.
- Tests: `pytest test/` (fast, no conda) and `test/run_demo.sh` (full run on
  the bundled demo, asserts exact STs) must both pass before a PR.
- One Snakemake rule per file in `workflow/rules/`; pinned versions in
  `workflow/envs/`.
- Keep the README usable by a microbiologist with no bioinformatics background:
  copy-pasteable commands, no unexplained jargon.

## Layout reminders

- Pipeline code: this repo (`~/nanotyper/` in the docs).
- User data and results: `~/nanotyper-projects/<project>/{data,analyses,combined}` — outside the repo.
- Design decisions: `docs/decisions/`. Read them before proposing architecture changes.
