.PHONY: install lint format typecheck test deptry check build

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

test:
	uv run pytest

deptry:
	uv run deptry .

check: lint typecheck deptry test

build:
	uv build
