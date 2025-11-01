# Configuration file for Sphinx to build our documentation to HTML.
#
# Configuration reference: https://www.sphinx-doc.org/en/master/usage/configuration.html
#
from datetime import datetime

# -- General Sphinx configuration ---------------------------------------------------
# ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
#
# Set the default role so we can use `foo` instead of ``foo``
default_role = "literal"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "jupyterhub_sphinx_theme",
    "sphinxcontrib.mermaid",
]

myst_enable_extensions = {"deflist"}

# The root toctree document.
root_doc = master_doc = "index"

# General information about the project.
project = "Site Reliability Guide for mybinder.org"
copyright = f"2017 - {datetime.now().year}, Binder Team"
author = "Binder Team"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# A string of reStructuredText that will be included at the end of every source file that is read.
with open("hyperlink-targets.md", encoding="utf-8") as _hyperlink_targets:
    rst_epilog = _hyperlink_targets.read()

# -- Options for HTML output ----------------------------------------------
# ref: http://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
#
html_theme = "jupyterhub_sphinx_theme"
html_theme_options = {
    "use_edit_page_button": True,
    "github_url": "https://github.com/jupyterhub/mybinder.org-deploy",
    "twitter_url": "https://twitter.com/mybinderteam",
}
html_context = {
    "github_user": "jupyterhub",
    "github_repo": "mybinder.org-deploy",
    # Branch name is needed to ensure the `Edit on GitHub` button works
    "github_version": "main",
    "doc_path": "docs/source",
}

html_static_path = ["_static"]
html_logo = "_static/images/logo.png"
html_favicon = "_static/images/favicon.png"


# -- Options for linkcheck builder -------------------------------------------
# ref: https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder
#
linkcheck_ignore = [
    r"(.*)github\.com(.*)#",  # javascript based anchors
    r"(.*)/#%21(.*)/(.*)",  # /#!forum/jupyter - encoded anchor edge case
    "https://grafana.mybinder.org",  # likely no longer functional links from incident reports
    "https://console.cloud.google.com",  # sign-in redirect noise
    "https://console.developers.google.com",  # sign-in redirect noise
]
linkcheck_anchors_ignore = [
    "/#!",
    "/#%21",
]
