# Changelog

## [Unreleased]

### Added

- Workflow facade: `client.files` and `client.retrievers` namespaces, and the
  full `AutoGraphProject` surface — `add_files` (folder/paths/glob, per-file
  `citable_urls`), `build()`/`orchestrate()` run handles with `.wait()`,
  blocking `strategize()` returning the plan, `deploy_retriever()` defaulting
  from persisted model settings, and `ask()`/`ask_stream()` with retriever
  resolution (explicit id > this handle's deploy > single one in metadata).
  `QueryResult` now prints as its answer. Quickstart example and README
  reflecting the real API. (AIS-1799)

<<<<<<< HEAD
- File Manager module (`FileManagerAPI`): chunked batch upload with
  per-file `custom_metadata` (e.g. `citable_url`, AIS-1740), folder upload
  with Studio-compatible filtering/flattening/dedupe and up-front key-budget
  and parser-size checks, file listing, category browsing, and deletion by
  id (incl. `not_found`) and by category. (AIS-1799)
- AutoGraph ingestion module (`arango_ai.autograph.ingestion.IngestionAPI`):
  corpus build with build-in-progress normalization, RAG strategizer
  (trigger with client-side complexity/image gates, plan read, per-cluster
  edit), knowledge-graph orchestration with secret-profile resolution from
  model settings, aggregate project overview, and two-tier waiters that
  fall back from the per-run status endpoints to the ACP metadata mirrors
  after a pod restart. New exception `BuildFailedError`. (AIS-1799)
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
