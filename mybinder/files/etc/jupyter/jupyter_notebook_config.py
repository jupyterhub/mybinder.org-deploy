import notebook
import os

from distutils.version import LooseVersion as V


c.NotebookApp.extra_template_paths.append('/etc/jupyter/templates')


# For old notebook versions we have to explicitly enable the translation
# extension
if V(notebook.__version__) < V('5.1.0'):
    c.NotebookApp.jinja_environment_options = {'extensions': ['jinja2.ext.i18n']}


binder_launch_host = os.environ.get('BINDER_LAUNCH_HOST', '')
binder_request = os.environ.get('BINDER_REQUEST', '')
binder_persistent_request = os.environ.get('BINDER_PERSISTENT_REQUEST', '')

repo_url = os.environ.get('BINDER_REPO_URL', '')

# Disable JITSI integration for now
jitsi_url = ''

c.NotebookApp.jinja_template_vars.update({
    'binder_url': binder_launch_host+binder_request,
    'persistent_binder_url': binder_launch_host+binder_persistent_request,
    'repo_url': repo_url,
    'ref_url': os.environ.get('BINDER_REF_URL', ''),
    'jitsi_url': jitsi_url,
})
