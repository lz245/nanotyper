# Provenance record for every analysis: which pipeline, scheme, database
# snapshot, medaka model, and tool versions produced results/.
# Written to results/provenance.yaml (docs/decisions/0009-database-snapshot-policy.md).

rule provenance:
    input:
        db_info = DB_INFO_FILE,
        scheme  = str(SCHEME_DIR / "scheme.yaml"),
        envs    = [str(PIPELINE_DIR / "workflow" / "envs" / f) for f in
                   ("medaka.yaml", "blast.yaml", "cutadapt.yaml", "python.yaml", "report.yaml")]
    output:
        yaml = RESULTS + "/provenance.yaml"
    params:
        version      = PIPELINE_VERSION,
        commit       = PIPELINE_COMMIT,
        scheme_name  = SCHEME_NAME,
        scheme_dir   = str(SCHEME_DIR),
        medaka_model = config["medaka"]["model"],
        qc           = config["qc"],
        blast        = config["blast"],
        cutadapt     = config["cutadapt"],
        samplesheet  = config["paths"]["samplesheet"]
    log:
        "logs/provenance.log"
    script:
        "../scripts/provenance.py"
