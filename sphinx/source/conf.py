# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from pathlib import Path
import sys


CURRENT_PATH = Path(__file__).parent.expanduser().resolve()
sys.path.insert(0, f'{CURRENT_PATH.parents[2]}/aioartifactory/')
print(f'{CURRENT_PATH.parents[1]}/aioartifactory/')

project = 'AIOArtifactory'
copyright = '2024, Yan Kuang'
author = 'Yan Kuang'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
