# Interactive HTML report (R Markdown).

rule report:
    input:
        summary = RESULTS + "/mlst_summary.tsv",
        long    = RESULTS + "/mlst_long.tsv",
        rmd     = "workflow/scripts/report.Rmd"
    output:
        html = RESULTS + "/mlst_report.html"
    params:
        version = PIPELINE_VERSION,
        commit  = PIPELINE_COMMIT
    log:
        "logs/report.log"
    conda:
        "../envs/report.yaml"
    shell:
        r"""
        set -euo pipefail
        Rscript -e "rmarkdown::render('{input.rmd}', \
            params = list(summary = '$(pwd)/{input.summary}', \
                          long    = '$(pwd)/{input.long}', \
                          version = '{params.version}', \
                          commit  = '{params.commit}'), \
            output_file = '$(pwd)/{output.html}', \
            intermediates_dir = tempdir(), \
            knit_root_dir = tempdir())" \
            > {log} 2>&1
        """
