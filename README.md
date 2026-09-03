# arango-ai-sdk

Python SDK for the **Arango AI Suite**. It wraps the suite's wire contracts so a developer
never handles endpoints, auth headers, JSON shapes, error codes, or polling loops directly.

The suite covers four services:

| Service                | Role                                                          |
| ---------------------- | ------------------------------------------------------------- |
| **ACP**                | Authentication and project management (system-wide)           |
| **FileManager**        | File upload and category/scope labeling (system-wide)         |
| **AutoGraph**          | Ingestion: corpus build, strategizing, orchestration          |
| **Retriever (AutoRag)**| Querying the built ContextGraph                               |

> **Status: scaffold.** No service surface exists yet. This repository currently proves the path
> from commit to installable package; the SDK's functionality arrives story by story. See the
> AI Suite SDK design document for scope, stages, and open questions.

## Installation

The package is published to the Arango **private** PyPI (Google Artifact Registry). Public PyPI
availability is a separate, later step.

Authentication to the registry uses Google Artifact Registry keyring support:

```bash
pip install keyring keyrings.google-artifactregistry-auth
gcloud auth login   # or supply a service-account key
```

With `pip`:

```bash
pip install arango-ai-sdk \
  --extra-index-url https://europe-west3-python.pkg.dev/arango-ml/arango-ml-internal-pypi/simple/
```

With `uv`, declare the index explicitly in the consuming project's `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "arango_private"
url = "https://europe-west3-python.pkg.dev/arango-ml/arango-ml-internal-pypi/simple/"
explicit = true

[tool.uv.sources]
arango-ai-sdk = { index = "arango_private" }
```

Then:

```python
import arango_ai_sdk

print(arango_ai_sdk.__version__)
```

## Development

The project is managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                  # create the environment
uv run pre-commit install  # enable the git hooks
make check               # lint + typecheck + dependency check + tests
```

Individual targets:

| Command           | What it runs                        |
| ----------------- | ----------------------------------- |
| `make lint`       | `ruff check`                        |
| `make format`     | `ruff format`                       |
| `make typecheck`  | `ty check`                          |
| `make deptry`     | dependency hygiene check            |
| `make test`       | `pytest`                            |
| `make build`      | `uv build` (wheel + sdist)          |
| `make docs`       | Sphinx user docs, see `docs/README.md` |

## Versioning and release channels

The version is **derived from the git tag** — it is not stored in any file, and there is nothing
to bump by hand. Which channel a build belongs to is encoded in the version itself, and installers
enforce the separation: `pip` and `uv` skip pre-releases unless asked. Assuming the latest tag is
`0.1.0rc1`:

| Git state           | Version produced               | Channel    | Who installs it      |
| ------------------- | ------------------------------ | ---------- | -------------------- |
| Any untagged commit | `0.1.0rc1.post1.dev3+g1a59664` | dev        | us, automatically    |
| Tagged `v0.1.0rc1`  | `0.1.0rc1`                     | QA         | QA, by asking for it |
| Tagged `v0.1.0`     | `0.1.0`                        | production | everyone             |

Releasing is therefore a tag, not a merge.

```bash
git tag -m "QA candidate" v0.1.0rc1   # tags are signed in arangoml org, so -m is required
git push origin v0.1.0rc1             # CI publishes 0.1.0rc1
```

## Open points

- **License** is not yet chosen. It must be settled before any public release.
