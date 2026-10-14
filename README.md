# arango-ai-sdk

![Work in Progress](https://img.shields.io/badge/status-work--in--progress-orange)

Python SDK for the **Arango AI Suite**. It wraps the suite's wire contracts so a developer
never handles endpoints, auth headers, JSON shapes, error codes, or polling loops directly.

The suite covers four services:

| Service                | Role                                                          |
| ---------------------- | ------------------------------------------------------------- |
| **ACP**                | Authentication and project management (system-wide)           |
| **FileManager**        | File upload and category/scope labeling (system-wide)         |
| **AutoGraph**          | Ingestion: corpus build, strategizing, orchestration          |
| **Retriever (AutoRag)**| Querying the built ContextGraph                               |

> **Status: work in progress.** The version 1 surface is in the repository. Publishing to
> public PyPI is a later step. Licensed under the Apache License 2.0.

## Install from this repository

Requires Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/arangoml/arango-ai-sdk
cd arango-ai-sdk
make install
```

`make install` runs `uv sync` and creates a virtual environment in `.venv`. Without `make`, as on
a default Windows setup, run `uv sync` directly. Activate the environment, then run any script
that imports the SDK from that shell:

```bash
source .venv/bin/activate          # macOS and Linux
.venv\Scripts\activate             # Windows
```

```python
import arango_ai_sdk

print(arango_ai_sdk.__version__)
```

## Install from the private index

The package is also published to the Arango **private** PyPI (Google Artifact Registry). Public
PyPI availability is a separate, later step.

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

## License

Apache License 2.0. See [LICENSE](LICENSE).
