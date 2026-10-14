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

# ArangoDB brand tokens (Figma Core Library tokens.json, platformUI style).
# The sidebar matches the platform shell: dark teal in both themes.
html_static_path = ["_static"]
html_css_files = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Geist+Mono&display=swap",
    "arango.css",
]
_sidebar = {
    "color-sidebar-background": "linear-gradient(#014654, #012d3a)",
    "color-sidebar-background-border": "#ffffff19",
    "color-sidebar-brand-text": "#befe99",
    "color-sidebar-caption-text": "#f8fafcb2",
    "color-sidebar-link-text": "#f8fafc",
    "color-sidebar-link-text--top-level": "#f8fafc",
    "color-sidebar-item-background--current": "#befe99",
    "color-sidebar-item-background--hover": "#06838a",
    "color-sidebar-item-expander-background--hover": "#06838a",
    "color-sidebar-search-background": "#ffffff0c",
    "color-sidebar-search-background--focus": "#ffffff16",
    "color-sidebar-search-border": "#ffffff19",
    "color-sidebar-search-foreground": "#f8fafc",
    "color-sidebar-search-icon": "#f8fafcb2",
}
html_theme_options = {
    "light_css_variables": {
        "font-stack": "Inter, sans-serif",
        "font-stack--monospace": "'Geist Mono', monospace",
        "color-brand-primary": "#00576e",
        "color-brand-content": "#00576e",
        "color-brand-visited": "#014654",
        "color-foreground-primary": "#1d293d",
        "color-foreground-secondary": "#62748e",
        "color-background-primary": "#ffffff",
        "color-background-secondary": "#f1f5f9",
        "color-background-hover": "#eefbd5",
        "color-background-border": "#e2e8f0",
        "color-code-background": "#f1f5f9",
        **_sidebar,
    },
    "dark_css_variables": {
        "color-brand-primary": "#befe99",
        "color-brand-content": "#befe99",
        "color-brand-visited": "#b0eb8f",
        "color-foreground-primary": "#f8fafc",
        "color-foreground-secondary": "#90a1b9",
        "color-background-primary": "#020618",
        "color-background-secondary": "#0f172b",
        "color-background-hover": "#1d293d",
        "color-background-border": "#ffffff19",
        "color-code-background": "#0f172b",
        **_sidebar,
    },
}
# Near the dark navy background; the default "native" is grey with underlined blue names.
pygments_dark_style = "github-dark"
