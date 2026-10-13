# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repository scaffold: `arango_ai_sdk` package (src layout, typed), uv project management,
  ruff/ty/pytest/deptry tooling, pre-commit hooks, and a smoke test suite.
- `Communication.send_request`: re-authenticates and retries once on `401`, and raises
  `ServiceError` with status code and message for every other non-success response.
- Sphinx user documentation under `docs/`: getting started, client and authentication,
  the projects and secret-profile namespaces, errors, and a generated API reference. Built with
  warnings-as-errors in CI (`make docs`).
- Vendor the ACP proto definitions under `proto/` and generate their betterproto data classes
  into `arango_ai_sdk._proto_out` (`make generate-proto`), replacing the `arango-platform-clients`
  dependency so the SDK installs from public PyPI alone.
- Project Manager returns a project handle on create and get.
- Files namespace (`client.files`): `upload_file`, `upload_files` and `upload_folder`.
- The request timeout can be overridden per call.
- `AiProjectHandle.autograph`: the project's single AutoGraph service.
- `AiProjectHandle.refresh()` reloads the project record from the platform.
- `ServiceApi` sends install and delete requests and maps ACP errors to SDK-specific errors.
- `ArangoAIClient(verify=...)`: TLS certificate verification can point at a CA bundle or be
  disabled, for deployments with a self-signed certificate.
- Run the integration tests in CI: a test image
  (`Dockerfile.test`), a chart carrying only a helm-test pod (`charts/arango-ai-sdk-tests`), and
  CircleCI jobs that build, register, and run it inside an ephemeral platform deployment,
  on feature branches, on `main`, and every night. Feature branches publish to the dev
  registries; `main` and release tags publish to qa, which is not pruned, so the nightly
  run always finds the chart it needs. The provider keys reach the test pod through a
  Secret, so they never appear in the pod spec, and are redacted from the debug package
  before it is stored as a CI artifact. Each test waits only for the services it calls. A failed publish or integration run on
  `main`, on a release tag or in the nightly run is reported to the team's Slack channel.
- A system test ingests the demo corpus and asks AutoRAG. It runs in the same
  integration job on `main` and nightly, with a 90 minute limit. Feature branches
  keep the short run and leave it out.
- Publish the user documentation to GitHub Pages on every push to `main` (`.github/workflows/docs.yml`).
- Document ingestion: `ingest`, `corpus_build`, `strategize`, `strategies` and `orchestrate` pages, their status models and exceptions.
- `AiProjectHandle.autorag`: deploy, list, get and remove the retrievers of a project, and ask one a question with `AutoRag.ask`.
- Document AutoRAG: deploy, list and get, ask and undeploy pages, the query
  response and `QueryType`, and `AutoRagNotDeployedError` and `QueryFailedError`.
