# Aggregate all per-sample MLST calls into a single wide summary.

rule aggregate:
    input:
        calls = expand(RESULTS + "/{sample}/mlst/{sample}_call.tsv", sample=SAMPLES),
        coverage = expand(RESULTS + "/{sample}/coverage/{sample}_locus_coverage.tsv", sample=SAMPLES),
        basecall = expand(RESULTS + "/{sample}/medaka/basecall_model.txt", sample=SAMPLES),
        samplesheet = config["paths"]["samplesheet"]
    output:
        summary = RESULTS + "/mlst_summary.tsv",
        long    = RESULTS + "/mlst_long.tsv",
        xlsx    = RESULTS + "/mlst_summary.xlsx"
    params:
        loci           = LOCI,
        min_share_pct  = config["qc"].get("min_locus_share_pct", 3),
        medaka_model   = config["medaka"]["model"]
    log:
        "logs/aggregate.log"
    conda:
        "../envs/python.yaml"
    script:
        "../scripts/aggregate.py"
