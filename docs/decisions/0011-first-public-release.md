# 0011 — First public release: v0.9.0 pre-release, v1.0.0 after validation

**Date**: 2026-08-27

**Decided**: publish the repository now under `github.com/lz245/nanotyper` and tag
**v0.9.0 as a GitHub pre-release**. **v1.0.0** follows once `docs/validation.md`, the
medaka model policy, and the QC-threshold decision (issues #1–#5) are done; the Zenodo
DOI is minted on v1.0.0 (issue #7) and that is the version the paper cites.

**Why**: the engineering is complete and CI-verified, but the QC label is known to be
dominated by *mdh* amplification efficiency (decision 0010) and the validation exists only
in a private note. Calling that "1.0" would be honest neither to users nor to reviewers;
calling it a release candidate is.

**Repository settings**: public; issues on, wiki/projects off; squash-merge; branch
protection on `main` requiring the `unit`, `lint`, `demo` checks and one review for pull
requests, not enforced for administrators (decision 0005). Milestone `v1.0` holds the
issues above; labels `science` / `engineering` / `docs` / `good-first-issue`.

**Rejected**: tagging v1.0.0 immediately (decision 0004's "ship sooner" was about the
GitHub home, not about skipping validation).
