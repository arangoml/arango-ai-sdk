# Changelog

## [Unreleased]

### Added

- File Manager module (`FileManagerAPI`): chunked batch upload with
  per-file `custom_metadata` (e.g. `citable_url`, AIS-1740), folder upload
  with Studio-compatible filtering/flattening/dedupe and up-front key-budget
  and parser-size checks, file listing, category browsing, and deletion by
  id (incl. `not_found`) and by category. (AIS-1799)
- Repository scaffold: poetry packaging (`arango-ai`, src layout, alpha
  classifiers), black/isort/flake8/mypy/bandit tooling with `_generated/`
  excluded everywhere, pre-commit, Makefile with codegen targets
  (`spec`, `generate-client`, `regen-check`), CircleCI pipeline
  (lint, test on 3.10/3.12, regen-check, changelog-check). (AIS-1799)
