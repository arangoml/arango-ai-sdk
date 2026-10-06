.PHONY: install lint format typecheck test deptry check build docs generate-openapi

install:
	uv sync

lint:
	uv run ruff check . --fix

format:
	uv run ruff format . # fix formatting, black compatible.

typecheck:
	uv run ty check

test:
	uv run pytest

deptry:
	uv run deptry .

check: lint format typecheck deptry test

build:
	uv build

# User documentation. -W turns every Sphinx warning into an error, --keep-going
# still reports all of them in one run. CI runs the same command.
docs:
	uv run --group docs sphinx-build -W --keep-going -b html docs docs/_build/html

# =============================================================================
# Proto Generation
# =============================================================================

PROTO_DIR = proto
PROTO_OUT = src/arango_ai_sdk/_proto_out
generate-proto: generate-secrets-proto generate-projects-proto generate-file-metadata-proto generate-genai-proto generate-corpus-graph-proto generate-retrievers-proto
	@echo "All proto files generated"



generate-secrets-proto:
	@echo "Generating secrets proto files..."
	@mkdir -p $(PROTO_OUT)
	@if [ -f "$(PROTO_DIR)/secrets.proto" ]; then \
		uv run python -m grpc_tools.protoc \
			-I=$(PROTO_DIR) \
			--python_betterproto_out=$(PROTO_OUT) \
			$(PROTO_DIR)/secrets.proto; \
		echo "Secrets proto files generated in $(PROTO_OUT)"; \
	else \
		echo "Warning: secrets.proto not found, skipping"; \
	fi

generate-projects-proto:
	@echo "Generating projects proto files..."
	@mkdir -p $(PROTO_OUT)
	@if [ -f "$(PROTO_DIR)/project_metadata.proto" ]; then \
		uv run python -m grpc_tools.protoc \
			-I=$(PROTO_DIR) \
			--python_betterproto_out=$(PROTO_OUT) \
			$(PROTO_DIR)/project_metadata.proto; \
		echo "Projects proto files generated in $(PROTO_OUT)"; \
	else \
		echo "Warning: project_metadata.proto not found, skipping"; \
	fi

generate-file-metadata-proto:
	@echo "Generating file metadata proto files..."
	@mkdir -p $(PROTO_OUT)
	@if [ -f "$(PROTO_DIR)/file_metadata.proto" ]; then \
		uv run python -m grpc_tools.protoc \
			-I=$(PROTO_DIR) \
			--python_betterproto_out=$(PROTO_OUT) \
			$(PROTO_DIR)/file_metadata.proto; \
		echo "File metadata proto files generated in $(PROTO_OUT)"; \
	else \
		echo "Warning: file_metadata.proto not found, skipping"; \
	fi

# =============================================================================
# OpenAPI Generation
# =============================================================================
# The file service publishes its API as OpenAPI documents, vendored under
# specs/. They are turned into pydantic models with the same datamodel-codegen
# options the service itself uses, so both sides read the same classes.

SPECS_DIR = specs
OPENAPI_OUT = src/arango_ai_sdk/_openapi_out
DATAMODEL_CODEGEN_ARGS = \
	--input-file-type openapi \
	--output-model-type pydantic_v2.BaseModel \
	--use-annotated \
	--field-constraints \
	--use-double-quotes \
	--target-python-version 3.12 \
	--collapse-root-models \
	--use-standard-collections \
	--use-union-operator \
	--use-subclass-enum \
	--output-datetime-class AwareDatetime

generate-openapi:
	@echo "Generating file service models from OpenAPI..."
	@mkdir -p $(OPENAPI_OUT)
	@uv run datamodel-codegen --input $(SPECS_DIR)/rag_input.yaml \
		--output $(OPENAPI_OUT)/rag_input.py $(DATAMODEL_CODEGEN_ARGS)
	@printf '%s\n' '"""Pydantic models generated from the OpenAPI documents under specs/.' \
		'' 'DO NOT EDIT DIRECTLY. Change the spec and run `make generate-openapi`.' '"""' \
		> $(OPENAPI_OUT)/__init__.py
	@echo "File service models generated in $(OPENAPI_OUT)"

generate-genai-proto:
	@echo "Generating genai proto files..."
	@mkdir -p $(PROTO_OUT)
	@if [ -f "$(PROTO_DIR)/genai.proto" ]; then \
		uv run python -m grpc_tools.protoc \
			-I=$(PROTO_DIR) \
			--python_betterproto_out=$(PROTO_OUT) \
			$(PROTO_DIR)/genai.proto; \
		echo "GenAI proto files generated in $(PROTO_OUT)"; \
	else \
		echo "Warning: genai.proto not found, skipping"; \
	fi

generate-corpus-graph-proto:
	@echo "Generating corpus graph proto files..."
	@mkdir -p $(PROTO_OUT)
	@if [ -f "$(PROTO_DIR)/corpus_graph.proto" ]; then \
		uv run python -m grpc_tools.protoc \
			-I=$(PROTO_DIR) \
			--python_betterproto_out=$(PROTO_OUT) \
			$(PROTO_DIR)/corpus_graph.proto; \
		echo "Corpus graph proto files generated in $(PROTO_OUT)"; \
	else \
		echo "Warning: corpus_graph.proto not found, skipping"; \
	fi

generate-retrievers-proto:
	@echo "Generating retrievers proto files..."
	@mkdir -p $(PROTO_OUT)
	@if [ -f "$(PROTO_DIR)/retrievers.proto" ]; then \
		uv run python -m grpc_tools.protoc \
			-I=$(PROTO_DIR) \
			--python_betterproto_out=$(PROTO_OUT) \
			$(PROTO_DIR)/retrievers.proto; \
		echo "Retrievers proto files generated in $(PROTO_OUT)"; \
	else \
		echo "Warning: retrievers.proto not found, skipping"; \
	fi
