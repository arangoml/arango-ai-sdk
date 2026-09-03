"""Sphinx configuration for the arango-ai-sdk user documentation.

Build with ``make docs`` from the repository root. The API reference is generated
by autodoc, which imports the installed package, so the ``docs`` dependency group
must be synced first: ``uv sync --group docs``.
"""

from arango_ai_sdk import __version__

# -- Project information -----------------------------------------------------

project = "arango-ai-sdk"
author = "ArangoDB AI Services"
copyright = "2026, ArangoDB"
release = __version__

# -- General configuration ---------------------------------------------------

# Everything here ships with Sphinx itself. No third-party extension is used, so
# the docs build cannot break on an extension falling behind a Sphinx release.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The code base documents with numpy-style sections (Parameters / Returns /
# Raises with dashed underlines), enforced by ruff's pydocstyle convention.
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# Parameters are described in the class docstring, not in __init__.
autoclass_content = "class"
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_title = f"{project} {release}"
html_copy_source = False
html_show_sourcelink = False
