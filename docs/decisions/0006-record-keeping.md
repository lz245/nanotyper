# 0006 — Record keeping for reproducibility

**Date**: 2026-08-26

**Decided**: two layers.
1. **Maintainer's notebook (private)** — the full design-conversation log and a decisions note, kept in the maintainer's Obsidian vault.
2. **Repository (shared)** — `docs/decisions/` mirrors every decision; `CHANGELOG.md` records what shipped.

Anything a contributor must know goes in the repository, never only in the private notebook.

**Why**: contributors do not have access to the maintainer's notebook; the repository must be self-explanatory for a reviewer or a future student.
