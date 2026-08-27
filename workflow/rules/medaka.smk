# Medaka consensus: per sample, FASTQ -> one multi-FASTA (one seq per locus).
# Reference is the 7-gene concatenated FASTA; medaka calls consensus per contig.

rule merge_fastq:
    """Concatenate barcode fastq.gz files into a single file for medaka."""
    input:
        # Snakemake will re-evaluate the directory each run. We use a checkpoint
        # semantic via `directory()` on the input path.
        lambda wc: samples.loc[wc.sample, "fastq_dir"]
    output:
        fastq = temp(RESULTS + "/{sample}/medaka/input.fastq.gz")
    log:
        "logs/merge_fastq/{sample}.log"
    shell:
        r"""
        set -euo pipefail
        shopt -s nullglob
        files=({input}/*.fastq.gz)
        if [ ${{#files[@]}} -eq 0 ]; then
            echo "ERROR: no .fastq.gz files found in {input}" >&2
            exit 1
        fi
        mkdir -p "$(dirname {output.fastq})"
        cat "${{files[@]}}" > {output.fastq} 2> {log}
        """

rule medaka_consensus:
    input:
        fastq = RESULTS + "/{sample}/medaka/input.fastq.gz",
        ref   = SCHEME_REFERENCE
    output:
        consensus = RESULTS + "/{sample}/consensus/{sample}_consensus.fasta"
    params:
        outdir = RESULTS + "/{sample}/medaka/run",
        model  = config["medaka"]["model"]
    log:
        "logs/medaka/{sample}.log"
    threads: config["medaka"]["threads"]
    conda:
        "../envs/medaka.yaml"
    shell:
        r"""
        set -euo pipefail
        rm -rf {params.outdir}
        medaka_consensus \
            -i {input.fastq} \
            -d {input.ref} \
            -o {params.outdir} \
            -t {threads} \
            -m {params.model} \
            > {log} 2>&1
        mkdir -p "$(dirname {output.consensus})"
        cp {params.outdir}/consensus.fasta {output.consensus}
        """
