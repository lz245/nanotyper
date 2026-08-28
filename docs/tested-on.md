# Tested on

Environments where the shipped demo (`test/run_demo.sh`) has been run end to end and
reported `all checks passed`. CI covers Ubuntu on every push; this file records the
machines real users and contributors actually installed on.

Add a row when you set up a new machine — see [How to add a row](#how-to-add-a-row).

| Date | OS | CPU | conda / mamba | snakemake | `run_demo.sh` wall clock | Demo |
|---|---|---|---|---|---|---|
| 2026-08-28 | Ubuntu 26.04 LTS on WSL2 (kernel 6.18.33.2-microsoft-standard-WSL2) | x86_64, Intel Core Ultra 7 265 (20 threads) | conda 26.3.2 / mamba 2.5.0 | 9.24.0 | 1 m 25 s [^warm] | ✅ all checks passed |

[^warm]: Of that, ~55 s was building the five per-rule conda environments and ~30 s was the
    pipeline itself (`-j 4`). The environments were created during this run, but from a conda
    package cache that already held the tool packages, so nothing was downloaded. On a machine
    with a cold cache, expect the first run to take roughly 15 minutes as `README.md` states;
    later runs reuse `--conda-prefix` and cost only the ~30 s of pipeline time.

## How to add a row

After `./install.sh` and a green `./test/run_demo.sh`, collect the values:

```bash
# OS and CPU
( . /etc/os-release && echo "$PRETTY_NAME" ) 2>/dev/null || sw_vers   # Linux / macOS
uname -srm

# toolchain
conda --version; mamba --version | head -1; snakemake --version

# wall clock (re-run; environments are already built, so this is the steady-state time)
time ./test/run_demo.sh
```

Report the wall clock you actually measured and say in a footnote whether the conda
environments were already built, since that dominates a first run. If the demo did **not**
end in `all checks passed`, do not add a row — open an issue with the output instead, because
a mismatched ST means the environment is wrong, not the machine's configuration.
