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
