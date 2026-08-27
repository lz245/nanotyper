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

# ---- basecalling models actually seen in the reads ----
# A model from a different chemistry than the medaka model leaves motif-specific
# errors that look like novel alleles (docs/decisions/0012-qc-thresholds.md).
basecall = {}
for f in snakemake.input.basecall:
    f = Path(f)
    try:
        basecall[f.parent.parent.name] = f.read_text().strip() or "unknown"
    except OSError:
        basecall[f.parent.parent.name] = "unknown"


def _family(model):
    m = (model or "").lower()
    for fam in ("r1041", "r10.4.1", "r104", "r10.4", "r941", "r9.4.1"):
        if fam in m:
            return fam.replace(".", "")
    return "unknown"


_medaka_family = _family(p.medaka_model)
_mismatched = sorted(s for s, m in basecall.items()
                     if _family(m) not in ("unknown", _medaka_family))

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
    "basecalling": {
        "models_seen": sorted(set(basecall.values())),
        "per_sample": dict(sorted(basecall.items())),
        "medaka_model_family": _medaka_family,
        "chemistry_mismatch_samples": _mismatched,
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
