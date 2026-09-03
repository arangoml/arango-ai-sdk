# Documentation

User documentation for `arango-ai-sdk`, built with [Sphinx](https://www.sphinx-doc.org/).
The audience is people who install and use the SDK, not people who develop it.

## Build

From the repository root:

```bash
uv sync --group docs   # once
make docs              # output in docs/_build/html/
```

`make docs` runs `sphinx-build -W --keep-going`: every warning is an error, and all of them
are reported in one run. CI runs the same command, so a page that does not build cannot be
merged. Typical causes are a page missing from a `toctree`, a `:ref:` to a label that does
not exist, or a code block without a blank line before it.

## Layout

```
docs/
├── conf.py                 Sphinx configuration
├── index.rst               Landing page and the top-level toctrees
├── getting-started/        Installation and the quickstart
├── client/                 The client and authentication
├── projects/               The `client.project` namespace
├── errors/                 The exception tree and how to catch
└── api/                    Reference generated from docstrings, one page per namespace
```

The rule the layout follows: **one directory per namespace, one page per operation, one
`api/<namespace>.rst` per namespace.** When a new area ships, say `client.files`, it gets

- `docs/files/index.rst` (what the area is, which operations exist) and
  `docs/files/upload.rst` (one page per operation);
- `docs/api/files.rst` with the `autoclass` directives;
- one line in each of the two toctrees in `docs/index.rst` and `docs/api/index.rst`.

Nothing else changes.

## Conventions

- **Areas, not services.** Write "projects", "files", "ingestion", "retrieval". Never name an
  internal service; service names are an implementation detail that changes over time.
- **Match the code.** Every code sample must run against the current signatures. The API
  pages are generated from the docstrings, so a wrong parameter description is fixed in the
  Python source, not in `docs/api/`.
- **Cross-reference with roles.** Use `` :class:`~arango_ai_sdk.ArangoAIClient` ``,
  `` :exc:`~arango_ai_sdk.exceptions.ServiceError` ``, `` :meth:` `` and `` :ref:`label` ``
  rather than bare backticks, so links stay correct when things move. The `~` shows only the
  last component.
- **Labels.** Each page that is linked to starts with a label: `.. _projects-create:`.
  Namespace overview pages use the namespace name (`.. _projects:`), operation pages use
  `namespace-operation`.
- **Docstrings are numpy style** (`Parameters` / `Returns` / `Raises` with dashed underlines),
  enforced by ruff. Napoleon renders them; nothing to do on the docs side.
- **Format is reStructuredText.** No Markdown parser is installed, so `.md` files under
  `docs/` (like this one) are not part of the build.
