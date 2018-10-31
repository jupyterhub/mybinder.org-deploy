import os
c.NotebookApp.extra_template_paths.append('/etc/jupyter/templates')
c.NotebookApp.jinja_template_vars.update({
    'binder_url': os.environ.get('BINDER_URL', 'https://mybinder.org'),
})
