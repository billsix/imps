# Configuration file for the Sphinx documentation builder.
# The Mario 64 "how a production game is built" book.

project = "How a Production Game Is Built"
copyright = "2026, William Emerison Six"
author = "William Emerison Six"
release = "0.0.1"

extensions = [
    "sphinx.ext.graphviz",   # .. graphviz:: / .. digraph:: figures
    "sphinx.ext.todo",
    "myst_parser",           # allow Markdown sources alongside rST if needed
]
myst_enable_extensions = ["colon_fence"]
todo_include_todos = True

# Code is C/C++ (the SM64 decomp + libultraship); default highlight to C.
highlight_language = "c"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML --------------------------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "How a Production Game Is Built"

# -- Graphviz ----------------------------------------------------------------
graphviz_output_format = "svg"

# -- LaTeX / PDF (LuaLaTeX for Unicode math like √ ∧ e₁) ----------------------
latex_engine = "lualatex"
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "11pt",
    "preamble": r"""
\usepackage{fontspec}
""",
}
