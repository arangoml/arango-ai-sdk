# arango-ai

> **Alpha (0.1.x): APIs may change without backward compatibility before 1.0.**

Python SDK for the Arango AI Suite. Drives the AutoGraph end-to-end workflow —
authenticate, upload documents, build the corpus graph, strategize, build the
knowledge graph, deploy a retriever, and query — through the platform gateway,
exactly the way AutoGraph Studio does.

```python
from arango_ai import Client

client = Client.from_env()  # ARANGO_URL, ARANGO_USERNAME, ARANGO_PASSWORD, ARANGO_DATABASE
project = client.autograph.create_project("demo", openai_api_key="sk-...")
project.add_files("./pdfs")
project.build().wait()
project.strategize(complexity="moderate")
project.orchestrate().wait()
project.deploy_retriever(chat_model="gpt-4.1")
print(project.ask("What does the corpus say about X?"))
```

## Design in one paragraph

Everything goes through the platform gateway with an ArangoDB JWT bearer — never
gRPC, never direct to pods. The transport layer is **generated** from the service
proto contracts (`make generate`, committed under `src/arango_ai/_generated/`,
excluded from lint so reviews focus on the hand-written code). The thin hand-written
facade owns what the wire contract cannot express: JWT lifecycle, polling and health
gates, multipart upload, the NDJSON query stream, and secret-profile plumbing. The
facade is the stable public API; the generated layer may churn between versions.

## Development

```
make install     # poetry install
make generate    # proto -> OpenAPI -> generated client
make regen-check # CI gate: committed generated code matches the spec
make lint test   # black/isort/flake8/mypy + pytest
```

Requires Python >= 3.10, `protoc`, and gnostic `protoc-gen-openapi`
(`go install github.com/google/gnostic/cmd/protoc-gen-openapi@latest`).

## Status

Private alpha for the PLG motion (AIS-1799). Scope: AutoGraph end-to-end plus
authentication. Platform-wide services, GAE, GraphML, and CoreDB wrapping come later.
