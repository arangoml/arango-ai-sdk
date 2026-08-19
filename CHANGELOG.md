# Changelog

## [Unreleased]

### Added

- Repository scaffold: poetry packaging (`arango-ai`, src layout, alpha
  classifiers), black/isort/flake8/mypy/bandit tooling with `_generated/`
  excluded everywhere, pre-commit, Makefile with codegen targets
  (`spec`, `generate-client`, `regen-check`), CircleCI pipeline
  (lint, test on 3.10/3.12, regen-check, changelog-check). (AIS-1799)
