# One-time setup: build per-locus BLAST DBs from PubMLST allele FASTAs.
# Idempotent — re-runs only if the .ndb is missing or older than the source.

rule build_blast_db:
    input:
        fasta = config["paths"]["allele_db_dir"] + "/{locus}.fasta"
    output:
        ndb = config["paths"]["allele_db_dir"] + "/{locus}.fasta.ndb"
    log:
        "logs/build_blast_db_{locus}.log"
    conda:
        "../envs/blast.yaml"
    shell:
        "makeblastdb -in {input.fasta} -dbtype nucl -parse_seqids "
        "-out {input.fasta} > {log} 2>&1"
