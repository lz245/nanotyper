# Validation

How we know nanotyper's calls are right, on which data, and where the limits are.

**Pipeline version**: 1.0.0 (thresholds and QC logic of `docs/decisions/0012-qc-thresholds.md`)
**Database**: PubMLST *E. coli* Achtman scheme, snapshot 2025-11-04 (16,242 STs; see `docs/decisions/0009-database-snapshot-policy.md`)
**Dataset**: 480 isolates, 5 sequencing runs, R10.4.1 flow cells, Dorado `dna_r10.4.1_e8.2_400bps_sup@v5.0.0`
**Reference method**: the Zhang lab's original bash ONT-MLST pipeline, run on the same reads

---

## 1. What was compared

nanotyper was run on five R10.4.1 runs (96 barcodes each) and every sample was matched
one-to-one, by (run, barcode), against the earlier pipeline's call for the same reads.
Both pipelines use medaka consensus → BLAST against PubMLST → profile lookup, but differ
in medaka version, thresholds, and QC logic, so agreement tests the re-implementation
rather than the biology.

| run | samples | matched | alleles agreeing on nanotyper `known` calls | alleles agreeing over all compared calls | STs agreeing |
|---|---|---|---|---|---|
| run003 | 96 | 96 | 607/607 | 607/672 | 69/69 |
| run004 | 96 | 96 | 635/635 | 635/672 | 67/67 |
| run011 | 96 | 96 | 563/563 | 563/672 | 46/46 |
| run012 | 96 | 96 | 599/599 | 599/672 | 59/59 |
| run013 | 96 | 96 | 590/590 | 590/672 | 46/46 |
| **total** | **480** | **480** | **2,994/2,994 (100 %)** | **2,994/3,360 (89.1 %)** | **287/287 (100 %)** |

**Read all three columns together.** Where nanotyper calls an allele `known` — a
full-length BLAST hit at 100 % identity — it agrees with the reference method on every
one of 2,994 calls, and the two pipelines agree on all 287 sequence types both were able
to assign. The 89.1 % figure is the same comparison *including* the 366 calls nanotyper
declines to call `known`: the older pipeline reported an allele number for those anyway.
Quoting 100 % without this sentence would overstate the result.

Of the 480 matched samples, the reference pipeline classified 287 as fully typed, 165 as
partial (at least one locus not called), and 28 as novel.

## 2. Effect of the calibrated thresholds

The thresholds were changed in 1.0.0 (`coverage_warn` 50× → 20×, `coverage_good`
unchanged at 100×) on the evidence in `docs/qc-calibration.md`. Re-running all 480
samples before and after:

| QC label | before (100/50) | after (100/20) | change |
|---|---|---|---|
| PASS | 179 | 179 | — |
| NEW_ST | 15 | 15 | — |
| NEW_ALLELE | 50 | 50 | — |
| LOW_COVERAGE | 94 | 154 | **+60** |
| FAIL | 142 | 82 | **−60** |

**No sequence type and no allele number changed for any of the 480 samples** (0 ST
differences, 0 allele differences). The relaxed FAIL boundary moved 60 samples from
`FAIL` to `LOW_COVERAGE`, which reports their tentative ST instead of withholding it —
it recovers information without altering a single call.

## 3. QC outcome on this dataset

| run | PASS | NEW_ST | LOW_COVERAGE | NEW_ALLELE | FAIL |
|---|---|---|---|---|---|
| run003 | 40 | 0 | 44 | 3 | 9 |
| run004 | 62 | 6 | 14 | 11 | 3 |
| run011 | 46 | 5 | 23 | 19 | 3 |
| run012 | 0 | 0 | 35 | 0 | 61 |
| run013 | 31 | 4 | 38 | 17 | 6 |

61 distinct sequence types were observed; the most frequent were ST349 (56 isolates),
ST8578 (44), ST69 (19), ST10 (18), ST155 (17) and ST362 (17).

Excluding run012 (below), the remaining 384 samples are 179 PASS, 15 NEW_ST, 119
LOW_COVERAGE, 50 NEW_ALLELE, 21 FAIL.

## 4. Limitations

**Legacy chemistry is out of scope.** Six further runs in this project (005–010) used
R9.4.1 or R10.4 flow cells with 2021-era Guppy models. nanotyper targets R10.4.1 and
later (`docs/decisions/0012-qc-thresholds.md`, addendum), so those runs are excluded from
every figure above. They are not merely unsupported — polishing them with a current
medaka model leaves motif-specific errors: imperfect BLAST matches occur at 12–21 % of
locus calls even above 200× depth, against 5.2 % on R10.4.1, with single mismatches
recurring at fixed positions (gyrB position 17, purA 237, icd 336/354, mdh 146). The
pipeline detects and flags such data rather than silently mis-calling it.

**run012 is a depth failure.** 61 of 96 barcodes FAIL and none reach PASS, and relaxing
the FAIL boundary from 50× to 20× did not rescue it. Its ST calls agree with the
reference method (59/59) but the run should be resequenced before its results are used.

**The `biological_id` replicate check found metadata errors, not calling errors.** All
three replicate groups in this dataset (6634, 6654, MS1440) disagree at **all seven
loci**, at coverages up to 14,115×, with both members labelled PASS or LOW_COVERAGE. Two
sequencings of one isolate cannot differ at every locus; these are different isolates,
i.e. a sample-tracking or `biological_id` assignment error at the bench. The check worked
as intended; the metadata needs correcting.

**A residual 5.2 % of locus calls are `new_allele` above 200× on supported chemistry.**
These are either genuinely novel alleles — the pinned PubMLST snapshot contains no
records submitted after 2024-12-31 — or residual consensus error. Distinguishing the two
requires authenticated PubMLST access or Sanger confirmation and is tracked in
[#9](https://github.com/lz245/nanotyper/issues/9). Treat `NEW_ALLELE` calls as candidates
for confirmation, not as findings.

**Primer balance limits depth, not the pipeline.** 456 of 480 samples carry a
`locus_balance_note`: *mdh* takes a median 2.5 % of a sample's on-target reads, so
roughly 3,900 reads per barcode are needed for *mdh* alone to reach 100×. This is a
primer-ratio property of the assay (see Jia et al. 2024, Fig. 2), reported rather than
compensated for.

**Not tested here**: organisms other than *E. coli* (only one scheme pack ships), and
macOS execution of the full pipeline (CI runs the unit tests on macOS but the end-to-end
demo only on Linux).

## 5. Reproducing this

```bash
# per-run results (five supported runs)
~/nanotyper/batch_run.sh ~/nanotyper-projects/<project>

# the calibration tables quoted above
~/nanotyper/tools/qc_calibration.py ~/nanotyper-projects/<project> \
    --exclude run005,run006,run007,run008,run009,run010 --out docs/qc-calibration.md
```

Every analysis writes `results/provenance.yaml` recording the pipeline version and commit,
the scheme pack, the PubMLST snapshot date and counts, the medaka model, the QC parameters,
and the pinned tool versions, so any call above can be traced to the exact configuration
that produced it.

## 6. Relationship to the published method

nanotyper re-implements and extends the ONT-MLST workflow of Jia et al. (2024),
*Poultry Science* 103:104067, [doi:10.1016/j.psj.2024.104067](https://doi.org/10.1016/j.psj.2024.104067).
It is not the code used in that paper: the published work used medaka 1.3.2 on the first
4,000 reads of R9.4 data, while nanotyper uses current medaka models on all reads and adds
primer-coverage QC, batch processing and the provenance record. The agreement reported
above is against the lab's own subsequent pipeline on R10.4.1 data, not against the
published R9.4 results.
