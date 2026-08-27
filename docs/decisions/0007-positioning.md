# 0007 — Positioning against prior art

**Date**: 2026-08-26

**Decided**: nanotyper is described as the **open, reproducible, automated** implementation of Nanopore amplicon MLST: Snakemake with pinned conda environments, formal QC tiers (PASS / NEW_ST / NEW_ALLELE / LOW_COVERAGE / FAIL), 96-plex batch mode with cross-run aggregation and replicate checks, and scheme packs.

It is a **successor to, not the code of,** Jia et al. 2024 (different medaka version and chemistry model, all reads instead of the first 4,000, new QC) and must always be described that way.

**Prior art**: Liou et al. 2020 (nanoMLST, MRSA) and García-Pérez et al. 2025 (NanoMLST, ESKAPE+E incl. *E. coli*, Krocus + manual Geneious, no code released). The second validated the wet lab but left analysis manual and closed — that gap is nanotyper's novelty claim.
