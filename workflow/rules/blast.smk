# BLAST consensus against each locus's allele DB.
# One output TSV per sample per locus; call_st aggregates.

rule blast_one_locus:
    input:
        consensus = RESULTS + "/{sample}/consensus/{sample}_consensus.fasta",
        allele_db = config["paths"]["allele_db_dir"] + "/{locus}.fasta",
        ndb       = config["paths"]["allele_db_dir"] + "/{locus}.fasta.ndb"
    output:
        tsv = RESULTS + "/{sample}/blast/{sample}_{locus}.tsv"
    params:
        max_target_seqs = config["blast"]["max_target_seqs"]
    log:
        "logs/blast/{sample}_{locus}.log"
    conda:
        "../envs/blast.yaml"
    shell:
        r"""
        set -euo pipefail
        mkdir -p "$(dirname {output.tsv})"
        blastn \
            -query {input.consensus} \
            -db {input.allele_db} \
            -outfmt "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore qlen slen" \
            -max_target_seqs {params.max_target_seqs} \
            -out {output.tsv} \
            2> {log}
        # Empty BLAST output is a legal result (no hit); do not fail.
        """
