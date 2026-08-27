# nanotyper demo dataset

Four *E. coli* MLST amplicon barcodes, subsampled from the Zhang lab's
2025-11 test run (R10.4.1 flow cell, SUP basecalling), sized so the pipeline
runs end-to-end in a few minutes at the **default QC thresholds**.

| barcode | sample | reads | expected |
|---|---|---|---|
| barcode01 | MS1545 | 7,000 of 16,305 | ST602, PASS |
| barcode02 | MS1559 | 7,000 of 13,388 | ST349, PASS |
| barcode03 | MS1469 | 7,000 of 8,226 | ST937, PASS |
| barcode04 | MS1467 | all 428 | FAIL (too few reads; exercises the failure path) |

Why 7,000 reads: the weakest locus (*mdh*) is only ~1.5–2 % of reads with
these primers, so ~7,000 reads are needed for every locus to reach the default
`coverage_good: 100`. Expected calls are in `expected.tsv` (ST + alleles from
the full-depth run; these STs are long-established and their allele numbers do
not change between PubMLST snapshots).

Rebuild from the lab's raw data (not needed by users): `tools/make_demo.py`
reads `manifest.tsv` (source folders, read counts, seed 42).

Run: `~/nanotyper/test/run_demo.sh` — runs the pipeline here and then
`test/check_demo.py` asserts the calls above.
