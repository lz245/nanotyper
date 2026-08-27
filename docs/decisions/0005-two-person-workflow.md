# 0005 — Two-person workflow (PI + student)

**Date**: 2026-08-26

**Decided**:
- Rules live in the repo: `CLAUDE.md` and `CONTRIBUTING.md`, so both people's AI coding sessions follow the same standards.
- GitHub Issues are the single task list; the release checklist becomes issues under a `v1.0` milestone. Branch protection on `main`: CI green + one review before merge.
- Division: PI owns scientific decisions (thresholds, validation design, scheme packs, manuscript); student owns engineering (fetch script, CI, demo data, tests).
- Data: demo subset in the repo; the full validation set on a non-purged shared location (not HPC scratch); SRA deposit eventually.

**Why**: the efficiency lever is shared rules, not tooling; scientific decisions must not be made in PR comments where they are lost.
