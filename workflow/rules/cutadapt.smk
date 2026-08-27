# Primer-coverage QC per sample.
# Uses cutadapt -g FWD -g REV in "linked" mode to count reads containing each primer pair.
# Output: one TSV per sample with columns (locus, fwd_count, rev_count, both_count).

rule cutadapt_coverage:
    input:
        fastq   = RESULTS + "/{sample}/medaka/input.fastq.gz",
        primers = SCHEME_PRIMERS
    output:
        tsv = RESULTS + "/{sample}/coverage/{sample}_locus_coverage.tsv"
    params:
        loci        = LOCI,
        error_rate  = config["cutadapt"]["error_rate"]
    log:
        "logs/cutadapt/{sample}.log"
    conda:
        "../envs/cutadapt.yaml"
    script:
        "../scripts/cutadapt_coverage.py"
