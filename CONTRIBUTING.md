# Contributing to nanotyper

nanotyper is developed by the Zhang lab at Mississippi State University. These
rules keep a two-person (PI + student) project reproducible and publishable.

## Workflow

1. **Every task is a GitHub Issue.** Pick one up by assigning yourself and
   commenting on it. Milestone `v1.0` is the release gate.
2. **Branch from `main`**, one branch per issue: `feat/<short-slug>`,
   `fix/<short-slug>`, `docs/<short-slug>`.
3. **Open a pull request** that references the issue (`Closes #12`). CI must
   pass; one review from the maintainer is required before merge. Squash-merge.
4. **Never commit data.** No `results/`, no `.fastq(.gz)`, no PubMLST
   downloads, no BLAST indexes. `.gitignore` enforces most of this — do not
   weaken it.
5. **Update `CHANGELOG.md`** under `[Unreleased]` in the same PR as the change.
6. **Before opening a PR**: `pytest test/`, `ruff check .`, and `test/run_demo.sh`
   must pass locally. CI runs the same three plus shellcheck.

## Division of responsibilities

| Area | Owner |
|---|---|
| Scientific decisions: QC thresholds, validation design, scheme packs, manuscript | Li Zhang (maintainer) |
| Engineering: fetch scripts, CI, tests, demo data, packaging | student developer |

Scientific decisions are not made in PR comments. They are recorded first (see below).

## Decision records

Any change to a scientific threshold, a database source, a reference sequence,
or the QC-label logic needs a short record in `docs/decisions/` before or with
the PR: `NNNN-<slug>.md` with **Decided / Why / Rejected** sections and a date.
These records become the Methods section of the paper; write them so a
reviewer could read them.

## Adding a scheme pack (planned layout — see `docs/decisions/0003-scheme-packs.md`)

```
schemes/<organism>_<scheme>/
  scheme.yaml       # organism, pubmlst_db, scheme_id, loci, amplicon sizes, default QC thresholds
  reference.fasta   # concatenated target genes for medaka
  primers.csv       # forward/reverse per locus
```

A new scheme is accepted only with: validated wet-lab primers, at least one
demo dataset with known STs, and a decision record explaining the thresholds.

## Code style

- Shell: `set -euo pipefail`, full tool names (never abbreviations), a USAGE
  block at the top of every standalone script with the exact command to run it.
- Python: formatted with `ruff format`, checked with `ruff check`.
- Snakemake: one rule per file under `workflow/rules/`, conda env per tool
  under `workflow/envs/` with pinned versions.
- Numbered output folders where order matters.

## Reporting problems

Open an issue with: the command you ran, the `run.log` from the analysis
folder, and the first failing line of the relevant `logs/<rule>/<sample>.log`.
