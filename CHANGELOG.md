# Changelog

## [Unreleased]

### Added

- Retrieval module (`arango_ai.retrieval`): `RetrieverAPI` with retriever
  deploy via ACP (chart `arangodb-graphrag-retriever`, secret profile ids
  only, chat/embedding credentials independent), a health-streak gate
  mirroring the Studio UI (3 consecutive healthy 200s; FAIL body or 5xx
  fails fast), streaming query over the NDJSON endpoint (`query_stream`
  with typed `TokenDelta`/`Progress`/`Final` events) and a blocking
  `query` built on top of it. (AIS-1799)

- Repository scaffold: poetry packaging (`arango-ai`, src layout, alpha
  classifiers), black/isort/flake8/mypy/bandit tooling with `_generated/`
  excluded everywhere, pre-commit, Makefile with codegen targets
  (`spec`, `generate-client`, `regen-check`), CircleCI pipeline
  (lint, test on 3.10/3.12, regen-check, changelog-check). (AIS-1799)
