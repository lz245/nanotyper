# One-time setup: build per-locus BLAST DBs from PubMLST allele FASTAs.
# Idempotent — re-runs only if the .ndb is missing or older than the source.

rule build_blast_db:
    input:
        fasta = ALLELE_DB_DIR + "/{locus}.fasta"
    output:
        ndb = ALLELE_DB_DIR + "/{locus}.fasta.ndb"
    log:
        "logs/build_blast_db_{locus}.log"
    conda:
        "../envs/blast.yaml"
    shell:
        "makeblastdb -in {input.fasta} -dbtype nucl -parse_seqids "
        "-out {input.fasta} > {log} 2>&1"
