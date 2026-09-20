# Configuration file for the Sphinx documentation builder.
# "How a Doom Engine Works" — reading the GZDoom source.

project = "How a Doom Engine Works"
copyright = "2026, William Emerison Six"
author = "William Emerison Six"
version = "0.0.1"
release = "0.0.1"

extensions = [
    "sphinx.ext.graphviz",   # .. graphviz:: / .. digraph:: figures
    "sphinx.ext.todo",
    "myst_parser",           # allow Markdown sources alongside rST if needed
]
myst_enable_extensions = ["colon_fence"]
todo_include_todos = True

# The code shown is GZDoom's engine source (C++).
highlight_language = "cpp"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML --------------------------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "How a Doom Engine Works"

# -- Graphviz ----------------------------------------------------------------
graphviz_output_format = "svg"

# -- LaTeX / PDF (LuaLaTeX, for any Unicode the prose uses) -------------------
latex_engine = "lualatex"
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "11pt",
    "preamble": r"""
\usepackage{fontspec}
""",
}
