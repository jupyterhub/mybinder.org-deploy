import notebook
import os

from distutils.version import LooseVersion as V


c.NotebookApp.extra_template_paths.append('/etc/jupyter/templates')


# For old notebook versions we have to explicitly enable the translation
# extension
if V(notebook.__version__) < V('5.1.0'):
    c.NotebookApp.jinja_environment_options = {'extensions': ['jinja2.ext.i18n']}


def make_federation_url(url):
    federation_host = 'https://mybinder.org'
    if not url:
        return ''
    url_parts = url.split('/v2/', 1)
    return federation_host + '/v2/' + url_parts[-1]


binder_url = make_federation_url(os.environ.get('BINDER_URL', ''))
persistent_binder_url = make_federation_url(os.environ.get('PERSISTENT_BINDER_URL', ''))

c.NotebookApp.jinja_template_vars.update({
    'binder_url': binder_url,
    'persistent_binder_url': persistent_binder_url,
    'repo_url': os.environ.get('REPO_URL', ''),
    'ref_url': os.environ.get('REF_URL', ''),
})
