# Changelog

## [Unreleased]

### Changed

- Quality pass: adversarial-review fixes across the SDK. Behavior fixes —
  id-less waiters no longer trust a previous run's terminal state from the
  metadata mirror (pre-trigger baseline/echo guard, UI parity); orchestrate
  no longer silently reuses the chat secret profile for embedding (the field
  is omitted unless explicitly configured); `create_project` validates
  credentials and the project name (ACP's `^[a-zA-Z][a-zA-Z0-9_-]{0,62}$`
  rule) before creating the ACP project, so a failed deploy can no longer
  orphan one; health gates count only 2xx as healthy and health probes no
  longer swallow SDK-typed errors (a failing token re-mint now surfaces as
  `AuthenticationError` instead of polling to timeout); long-running waiters
  (corpus build, strategize, orchestration, service deploy) tolerate up to 5
  consecutive transient poll failures (transport errors, 5xx) instead of
  aborting on the first blip; upload chunks get a generous 600s timeout and
  a transport error on one chunk fails only that chunk's files (outcome
  marked unknown) while the remaining chunks still upload; query streams
  wrap transport errors as `APITimeoutError`/`APIConnectionError`;
  user-influenced URL path segments (project names) are percent-encoded and
  `citable_urls` now applies to `FileUpload` entries and rejects unmatched
  names instead of dropping them silently; `project.delete()` returns one
  normalized `{"deleted", "warnings"}` shape on both phases;
  `QueryResult.progress` carries typed `Progress` objects (same as the
  stream yields); `list_secret_profiles` rejects provider combined with
  pagination up front; `build_autograph_env` enforces api_url for custom
  providers like its retriever twin. Renames: `serving_timeout` and
  `healthy_timeout` are unified as `health_timeout` (create_project,
  retriever deploy), and `deploy_retriever` gained
  `deploy_timeout`/`health_timeout` passthroughs. The new exception surface
  from the core hardening (per-status `ApiError` subclasses such as
  `NotFoundError`/`ConflictError`/`InternalServerError`, plus
  `APIConnectionError`/`APITimeoutError` transport wrapping) is now pinned
  by tests. (AIS-1799)

### Added

- First-class async support: `AsyncClient` with 1:1 mirrored namespaces and
  method signatures (`acp`, `autograph`, `files`, `retrievers`), the
  `AsyncAutoGraphProject` facade (incl. `AsyncCorpusBuildRun` /
  `AsyncOrchestrationRun` handles), `AsyncJwtAuth` with the same
  proactive-refresh and retry-once-on-401 semantics, async polling waiters,
  and an async `query_stream` over the NDJSON endpoint. Sync and async twins
  share all non-I/O logic (bodies, validation, frame parsing, terminal-state
  handling) through common module helpers. (AIS-1799)
- Workflow facade: `client.files` and `client.retrievers` namespaces, and the
  full `AutoGraphProject` surface — `add_files` (folder/paths/glob, per-file
  `citable_urls`), `build()`/`orchestrate()` run handles with `.wait()`,
  blocking `strategize()` returning the plan, `deploy_retriever()` defaulting
  from persisted model settings, and `ask()`/`ask_stream()` with retriever
  resolution (explicit id > this handle's deploy > single one in metadata).
  `QueryResult` now prints as its answer. Quickstart example and README
  reflecting the real API. (AIS-1799)
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
