# arango-ai

> **Alpha (0.1.x): APIs may change without backward compatibility before 1.0.**

Python SDK for the Arango AI Suite. Drives the AutoGraph end-to-end workflow —
authenticate, upload documents, build the corpus graph, strategize, build the
knowledge graph, deploy a retriever, and query — through the platform gateway,
exactly the way AutoGraph Studio does.

## Quickstart

```python
import os
from arango_ai import Client

client = Client.from_env()  # ARANGO_URL, ARANGO_USERNAME, ARANGO_PASSWORD, ARANGO_DATABASE

# Project + service onboarding in one call (secret profile, deploy, health gate).
project = client.autograph.create_project(
    "demo", openai_api_key=os.environ["OPENAI_API_KEY"]
)

project.add_files("./docs", category="knowledge")   # folder, paths, or a glob
project.build().wait()                              # corpus graph
project.strategize("moderate")                      # strategy plan (returns it for review)
project.orchestrate().wait()                        # knowledge graph
project.deploy_retriever()                          # reuses the project's model settings
print(project.ask("What are the main topics in these documents?"))
```

Streaming, deep search, and per-file citation URLs:

```python
project.add_files(
    ["report.pdf"], citable_urls={"report.pdf": "https://example.com/report"}
)
for event in project.ask_stream("Summarize the findings", mode="DEEP_SEARCH"):
    ...  # TokenDelta / Progress events, then one Final
```

## Design in one paragraph

Everything goes through the platform gateway with an ArangoDB JWT bearer — never
gRPC, never direct to pods. The transport layer is **generated** from the service
proto contracts (`make generate`, committed under `src/arango_ai/_generated/`,
excluded from lint so reviews focus on the hand-written code). The thin hand-written
facade owns what the wire contract cannot express: JWT lifecycle, polling and health
gates, multipart upload, the NDJSON query stream, and secret-profile plumbing. The
facade is the stable public API; the generated layer may churn between versions.

## API layers

| Layer | Entry point | What it wraps |
|-------|-------------|---------------|
| Workflow facade | `client.autograph.create_project(...)` -> `AutoGraphProject` | the whole load -> build -> retrieve flow |
| File Manager | `client.files` | batch upload, categories, list, delete |
| ACP control plane | `client.acp` | projects, secret profiles, service deploys |
| Retrievers | `client.retrievers` | deploy, health gate, streaming + blocking query |

The facade methods are thin delegates to these namespaces, so anything the
facade does can also be driven directly.

## Development

```
make install     # poetry install
make generate    # proto -> OpenAPI -> generated client
make regen-check # CI gate: committed generated code matches the spec
make lint test   # black/isort/flake8/mypy + pytest
```

Requires Python >= 3.10. Codegen additionally needs `protoc` and gnostic
`protoc-gen-openapi` (`make tools`).

## Versioning

Pre-1.0 this package generally follows SemVer with the usual pre-1.0 caveat:
minor versions (0.2, 0.3, ...) may contain backwards-incompatible changes.
Pin tutorials and notebooks to a compatible range, e.g. `arango-ai~=0.1`.

## Status

Private alpha for the PLG motion (AIS-1799). Scope: AutoGraph end-to-end plus
authentication. Platform-wide services, GAE, GraphML, and CoreDB wrapping come later.
