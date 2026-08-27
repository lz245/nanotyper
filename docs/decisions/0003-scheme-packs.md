# 0003 — Architecture: scheme packs

**Date**: 2026-08-26

**Decided**: everything organism-specific lives in one directory per scheme:

```
schemes/<organism>_<scheme>/
  scheme.yaml       # organism, pubmlst_db, scheme_id, loci, amplicon sizes, default QC thresholds
  reference.fasta   # concatenated target genes for medaka
  primers.csv       # forward/reverse per locus
```

`config.yaml` selects `scheme: ecoli_achtman`; the PubMLST fetch script reads `scheme.yaml`. Adding an organism = adding a folder + validating it. The medaka model stays in run-level config because it is chemistry-specific, not organism-specific.

**Known future exception**: *Salmonella* 7-gene MLST lives on EnteroBase, not PubMLST — a second fetcher, out of scope for v1.0.

**Why**: the pipeline is already ~90 % organism-agnostic (loci from config, per-locus allele FASTAs, profile table, concatenated reference, primer CSV); only five items are *E. coli*-specific and they all fit in one folder.

**Status**: layout decided; implementation is a separate step (the current `resources/databases` symlink is replaced by the first scheme pack).
