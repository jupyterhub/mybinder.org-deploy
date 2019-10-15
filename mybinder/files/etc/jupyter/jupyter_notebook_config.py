import os
c.NotebookApp.extra_template_paths.append('/etc/jupyter/templates')

federation_host = 'https://mybinder.org'
current_hosts = ['https://gke.mybinder.org', 'https://ovh.mybinder.org']
binder_url = os.environ.get('BINDER_URL', federation_host)
persistent_binder_url = os.environ.get('PERSISTENT_BINDER_URL', '')
for h in current_hosts:
    binder_url = binder_url.replace(h, federation_host)
    persistent_binder_url = persistent_binder_url.replace(h, federation_host)

c.NotebookApp.jinja_template_vars.update({
    'binder_url': binder_url,
    'persistent_binder_url': persistent_binder_url,
    'repo_url': os.environ.get('REPO_URL', ''),
    'ref_url': os.environ.get('REF_URL', ''),
})
