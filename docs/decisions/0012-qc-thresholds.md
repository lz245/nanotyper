# 0012 — QC thresholds, locus balance, and basecalling-model detection

**Date**: 2026-08-27 · Issue [#3](https://github.com/lz245/nanotyper/issues/3)

## Decided

1. **`coverage_warn: 50 → 20`**, `coverage_good` stays 100. A locus between 20× and
   99× is `LOW_COVERAGE` (allele reported with its tentative ST) rather than `FAIL`.
2. **No per-locus thresholds.** The imbalance between loci is a primer-ratio problem;
   the pipeline reports it instead of compensating for it.
3. **Locus-balance QC** (new): per-sample `<locus>_share_pct` columns, a
   `locus_balance_note` for any locus below `qc.min_locus_share_pct` (default 3 %),
   and a report panel that converts the weakest share into the reads-per-barcode
   actually needed to clear `coverage_good`.
4. **Basecalling-model detection** (new): `basecall_model_version_id` is read from each
   barcode's FASTQ headers, recorded per sample and in `provenance.yaml`, and the report
   warns when its chemistry family disagrees with the medaka model in use. Detection
   only — model *selection* is [#2](https://github.com/lz245/nanotyper/issues/2).
5. Every threshold in the report is now driven by the config; none are hard-coded.

## Why

Evidence: `docs/qc-calibration.md`, regenerable with
`tools/qc_calibration.py <project> --exclude test,scheme-pack-check` over the
952-sample, 11-run APEC project.

**The thresholds.** On the five 2025 runs (R10.4.1, SUP v5 — the chemistry the default
medaka model is for), the rate of locus calls that miss a known allele falls as depth
rises: ~32–38 % below 20×, ~21–26 % from 20–50×, 19.9 % at 50–100×, 15.8 % at 100–200×,
**5.2 % above 200×**. There is no discontinuity between 20–50× and 50–100×, so the old
50× FAIL boundary discarded usable calls; the real cliff is below 20×. The legacy bash
pipeline used PASS ≥50 / WARNING ≥20 on the same data, and Jia et al. (2024) found 400
reads per isolate adequate — both consistent with 20× as the floor. Effect on the 2025
runs: FAIL 142 → 82; those 60 samples become `LOW_COVERAGE` with their ST visible.

**Why not per-locus thresholds.** *mdh* takes a median 2.5 % of a sample's on-target
reads (*purA* 33 %, *adk* 20 %), so *mdh* is the weakest locus in 516 of 952 samples and
needs ~3,900 reads per barcode to reach 100× on its own. Lowering the *mdh* threshold
would hide that; the honest fix is the primer ratio at the bench (Jia et al. 2024,
Fig. 2 — the same imbalance the paper addressed). The report now states the required
read count instead.

**Why model detection matters.** The project mixes chemistries — five 2025 runs
(R10.4.1/SUP v5) and six 2022 runs (R9.4.1 or R10.4, 2021 Guppy models) — all polished
with an `r1041` medaka model. At ≥200× the `new_allele` rate is 5.2 % (r1041) versus
12.2 % (r941) and 20.8 % (r104). The excess is systematic, not biological: single
mismatches recur at fixed positions — gyrB allele position 17 T→C in 124 samples across
six unrelated allele backgrounds (runs 006–008 only), purA:237 T→C in 88 samples (runs
005/009/010 only), plus icd:336/354 and mdh:146. Pileups from `calls_to_draft.bam` show
42–44 % C at gyrB:17 in every run008 sample versus 3 % in run003. A mismatched model
cannot correct a motif the basecaller got wrong, so the pipeline must say so.

## Rejected

- **Per-locus or share-normalised coverage thresholds** — hides a wet-lab problem and
  makes thresholds unportable between primer sets.
- **Lowering `coverage_good` below 100** — the error rate is still ~16 % at 100–200×;
  PASS should mean something.
- **Auto-selecting the medaka model now** — needs the R9/R10 policy decision in #2.

## Consequences

- Previously published labels change: re-run or re-label before quoting PASS rates.
- `NEW_ALLELE` counts on the 2022 runs must not be read as biology until #2 is settled;
  the residual 5.2 % on clean chemistry is tracked in
  [#9](https://github.com/lz245/nanotyper/issues/9).
- New summary columns: `<locus>_share_pct`, `locus_balance_note`, `basecall_model`,
  `model_note`; new long-format column `share_pct`.
