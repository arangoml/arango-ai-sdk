.PHONY: install lint format typecheck test deptry check build

install:
	uv sync

format:
	uv run ruff check . --fix # fix problems the linter finds.
	uv run ruff format . # fix formatting, black compatible.

typecheck:
	uv run ty check

test:
	uv run pytest

deptry:
	uv run deptry .

check: lint typecheck deptry test

build:
	uv build
