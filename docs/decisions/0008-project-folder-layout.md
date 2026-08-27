# 0008 — Project-folder layout for data and results

**Date**: 2026-08-26

**Decided**: all nanotyper studies live under one umbrella, one folder per study, with raw data and results as siblings:

```
~/nanotyper/                              # code (git)
~/nanotyper-projects/<YYYY-MM_study>/
    data/<run>/fastq_pass/…  + samplesheet.csv     # raw, read-only
    analyses/<run>/{samplesheet.csv, fastq_pass -> ../../data/<run>/fastq_pass, results/}
    combined/                                       # cross-run outputs
    batch.log
```

`batch_run.sh` takes the project folder as its only positional argument and creates **relative** symlinks.

**Why**: one study = one self-contained, movable, zip-able record; matches the maintainer's existing per-study folder convention for other pipelines; relative symlinks survive moving the folder to a NAS or archive.

**Rejected**: two home-level roots (`~/<tool>-data`, `~/<tool>-analyses`) with absolute symlinks — scattered a study across trees and broke on any move.
