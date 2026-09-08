.PHONY: install lint format typecheck test deptry check build docs

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
generate-proto: generate-secrets-proto generate-projects-proto generate-file-metadata-proto
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
