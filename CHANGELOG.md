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
