# Aggregate all per-sample MLST calls into a single wide summary.

rule aggregate:
    input:
        calls = expand(RESULTS + "/{sample}/mlst/{sample}_call.tsv", sample=SAMPLES),
        coverage = expand(RESULTS + "/{sample}/coverage/{sample}_locus_coverage.tsv", sample=SAMPLES),
        samplesheet = config["paths"]["samplesheet"]
    output:
        summary = RESULTS + "/mlst_summary.tsv",
        long    = RESULTS + "/mlst_long.tsv",
        xlsx    = RESULTS + "/mlst_summary.xlsx"
    params:
        loci = LOCI
    log:
        "logs/aggregate.log"
    conda:
        "../envs/python.yaml"
    script:
        "../scripts/aggregate.py"
