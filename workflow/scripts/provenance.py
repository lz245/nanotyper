"""
Write results/provenance.yaml: everything needed to reproduce this analysis.
Runs in the Snakemake base environment (only PyYAML + stdlib).
"""
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

p = snakemake.params
out = Path(snakemake.output.yaml)

# ---- PubMLST snapshot metadata from database_info.txt ----
db_text = Path(snakemake.input.db_info).read_text()
def grab(pattern, default=None):
    m = re.search(pattern, db_text, re.M)
    return m.group(1).strip() if m else default
alleles = {m.group(1): int(m.group(2)) for m in re.finditer(r"^\s+(\w+): (\d+) alleles", db_text, re.M)}

scheme = yaml.safe_load(Path(snakemake.input.scheme).read_text())

# ---- pinned tool versions from the conda env files ----
tools = {}
for env_file in snakemake.input.envs:
    env = yaml.safe_load(Path(env_file).read_text())
    for dep in env.get("dependencies", []):
        if isinstance(dep, str) and "=" in dep:
            name, ver = dep.split("=", 1)
            tools[name] = ver

record = {
    "nanotyper": {"version": p.version, "commit": p.commit},
    "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    "samplesheet": p.samplesheet,
    "scheme": {
        "name": p.scheme_name,
        "organism": scheme.get("organism"),
        "description": scheme.get("description"),
        "loci": list(scheme.get("loci", [])),
        "directory": p.scheme_dir,
    },
    "pubmlst_snapshot": {
        "downloaded": grab(r"^# Downloaded: (.+)$"),
        "source": grab(r"^# Source: (.+)$"),
        "scheme_id": grab(r"^# Scheme ID: (.+)$"),
        "access_restriction": grab(r"^# Restriction: (.+)$", "not recorded"),
        "alleles": alleles,
        "total_sts": int(grab(r"^\s+Total STs: (\d+)", "0")),
    },
    "parameters": {
        "medaka_model": p.medaka_model,
        "blast": dict(p.blast),
        "cutadapt": dict(p.cutadapt),
        "qc": dict(p.qc),
    },
    "tool_versions": tools,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(yaml.safe_dump(record, sort_keys=False))
Path(snakemake.log[0]).write_text(f"wrote {out}\n")
