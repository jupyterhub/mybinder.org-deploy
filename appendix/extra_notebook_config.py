import os
c.NotebookApp.extra_template_paths.append('/etc/jupyter/binder_templates')
c.NotebookApp.jinja_template_vars.update({
    'binder_url': os.environ.get('BINDER_URL', 'https://mybinder.org'),
})

# shutdown notebook after no activity for 10 minutes
c.NotebookApp.shutdown_no_activity_timeout = 10 * 60
# shutdown idle kernels after 10 minutes
c.MappingKernelManager.cull_idle_timeout = 10 * 60
# check kernel idleness every minute
c.MappingKernelManager.cull_interval = 60
# a kernel with open connections but no activity still counts as idle
# this is what allows us to shutdown servers when people leave a notebook open and wander off
c.MappingKernelManager.cull_connected = True
