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
