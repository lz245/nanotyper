# Per-sample MLST call: read 7 BLAST TSVs, call alleles, look up ST, assign QC.

rule call_st:
    input:
        blast_tsvs = expand(RESULTS + "/{{sample}}/blast/{{sample}}_{locus}.tsv", locus=LOCI),
        coverage   = RESULTS + "/{sample}/coverage/{sample}_locus_coverage.tsv",
        profiles   = config["paths"]["profile_file"]
    output:
        call_tsv = RESULTS + "/{sample}/mlst/{sample}_call.tsv"
    params:
        loci            = LOCI,
        min_identity    = config["blast"]["min_identity"],
        require_full    = config["blast"]["require_full_length"],
        coverage_good   = config["qc"]["coverage_good"],
        coverage_warn   = config["qc"]["coverage_warn"]
    log:
        "logs/call_st/{sample}.log"
    conda:
        "../envs/python.yaml"
    script:
        "../scripts/call_st.py"
