# Interactive HTML report (R Markdown).

rule report:
    input:
        summary = RESULTS + "/mlst_summary.tsv",
        long    = RESULTS + "/mlst_long.tsv",
        rmd     = REPORT_RMD
    output:
        html = RESULTS + "/mlst_report.html"
    params:
        version  = PIPELINE_VERSION,
        commit   = PIPELINE_COMMIT,
        scheme   = SCHEME_NAME,
        organism = SCHEME["organism"],
        db_date  = DB_DATE,
        cov_good = config["qc"]["coverage_good"],
        cov_warn = config["qc"]["coverage_warn"],
        medaka_model = config["medaka"]["model"]
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
                          commit  = '{params.commit}', \
                          scheme  = '{params.scheme}', \
                          organism = '{params.organism}', \
                          db_date = '{params.db_date}', \
                          cov_good = {params.cov_good}, \
                          cov_warn = {params.cov_warn}, \
                          medaka_model = '{params.medaka_model}'), \
            output_file = '$(pwd)/{output.html}', \
            intermediates_dir = tempdir(), \
            knit_root_dir = tempdir())" \
            > {log} 2>&1
        """
