# Codegen tool pins. Regeneration must be deterministic: the committed
# generated client is a build artifact reviewers diff mechanically, and
# regen-check proves it matches the committed spec.
PROTOC_GEN_OPENAPI_VERSION = v0.7.1

SPEC_DIR = specs
GEN_DIR  = src/arango_ai/_generated

.PHONY: install fmt lint test tools spec generate-client generate regen-check

install:
	poetry install

fmt:
	poetry run black src tests
	poetry run isort src tests

lint:
	poetry run black --check src tests
	poetry run isort --check-only src tests
	poetry run flake8 src tests
	poetry run mypy
	poetry run bandit -c pyproject.toml -q -r src

test:
	poetry run pytest

tools:
	go install github.com/google/gnostic/cmd/protoc-gen-openapi@$(PROTOC_GEN_OPENAPI_VERSION)

# proto -> OpenAPI 3 (gnostic). enum_type=string so enums travel as the value
# names grpc-gateway accepts on the wire (what AutoGraph Studio sends).
# Requires protoc and protoc-gen-openapi locally (make tools); runs locally
# when the vendored proto is bumped -- CI does not repeat this half, it
# re-runs only the python half from the committed spec (see regen-check).
spec:
	PATH="$$PATH:$$HOME/go/bin" protoc -I $(SPEC_DIR)/proto \
		--openapi_out=enum_type=string:$(SPEC_DIR) \
		$(SPEC_DIR)/proto/corpus_graph.proto
	mv $(SPEC_DIR)/openapi.yaml $(SPEC_DIR)/autograph.openapi.yaml

# OpenAPI -> python client (committed, lint-excluded, reviewed as artifact).
# No-op while no spec is committed yet (pre-codegen scaffold) so regen-check
# stays green on the scaffold branch.
# The generator's own post-hooks are disabled (specs/openapi-python-client.yml)
# because they resolve `ruff` from the environment, which made output differ
# between local and CI. Formatting runs here instead, via the venv-pinned ruff.
generate-client:
	@if [ ! -f $(SPEC_DIR)/autograph.openapi.yaml ]; then \
		echo "no committed spec yet - skipping client generation"; \
	else \
		rm -rf $(GEN_DIR)/autograph && \
		poetry run openapi-python-client generate \
			--path $(SPEC_DIR)/autograph.openapi.yaml \
			--config $(SPEC_DIR)/openapi-python-client.yml \
			--output-path $(GEN_DIR)/autograph --meta none && \
		poetry run ruff check --fix-only --quiet $(GEN_DIR)/autograph && \
		poetry run ruff format --quiet $(GEN_DIR)/autograph; \
	fi

generate: spec generate-client

# CI gate: regenerating the client from the committed spec must be a no-op.
# Catches hand-edits under _generated/ and spec/client drift.
regen-check: generate-client
	git diff --exit-code -- $(SPEC_DIR) $(GEN_DIR) || \
		(echo "Generated code is stale: run 'make generate' and commit." && exit 1)
