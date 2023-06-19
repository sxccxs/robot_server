# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(".."))
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "robot-server"
copyright = "2023, Hryhorii Biloshenko"
author = "Hryhorii Biloshenko"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

napoleon_google_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_param = True

autodoc_default_options = {
    "member-order": "bysource",
    "special-members": "__slots__",
}

autodoc_docstring_signature = True
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
autodoc_inherit_docstrings = True

napoleon_type_aliases = autodoc_type_aliases = {
    "ServerCommandWithoutArgument": "ServerCommandWithoutArgument",
    "StringCommands": "StringCommands",
    "NumberCommands": "NumberCommands",
    "NoneValueCommands": "NoneValueCommands",
    "Result": "Result",
    "NoneResult": "NoneResult",
    "ServerResult": "ServerResult",
    "NoneServerResult": "NoneServerResult",
}
