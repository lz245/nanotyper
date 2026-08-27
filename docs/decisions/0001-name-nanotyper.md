# 0001 — Name: nanotyper

**Date**: 2026-08-26

**Decided**: the tool, repository and package are named **nanotyper** (previously `ont-mlst-snakemake`).

**Why**: pairs with the lab's existing public tool `nano16s`; "typer" is scheme-agnostic so serotyping or cgMLST packs fit later without a rename. Verified free on GitHub (name search), PyPI (JSON API, with a nonsense-name control), Bioconda, conda-forge, Docker Hub, and web search for published tools, on 2026-08-26.

**Rejected**:
- `nanomlst` — two published tools already use it: Liou et al. 2020, *Microbial Genomics*, doi:10.1099/mgen.0.000336 (`jade-nhri/nanoMLST`, MRSA, unmaintained since 2019) and García-Pérez et al. 2025, *MicrobiologyOpen* 14(6):e70204 (ESKAPE+E incl. *E. coli*, Krocus + Geneious, no code released). Same name would cause permanent citation confusion.
- `poretyper` — free, but weaker link to nano16s and sounds like `poretools`.
- `mlstpore` — free, but locks the name to classical MLST, contradicting 0003.
- `ont-*` prefixes — imply Oxford Nanopore affiliation (ONT uses `ont-` for official packages).
