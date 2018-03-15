import os
c.NotebookApp.extra_template_paths.append('/etc/jupyter/binder_templates')
c.NotebookApp.jinja_template_vars.update({
    'binder_url': os.environ.get('BINDER_URL', 'https://mybinder.org'),
})


# if a user leaves a notebook with a running kernel,
# the effective idle timeout will typically be CULL_TIMEOUT + CULL_KERNEL_TIMEOUT
# as culling the kernel will register activity,
# resetting the no_activity timer for the server as a whole

if os.getenv('CULL_TIMEOUT'):
    # shutdown the server after no activity
    c.NotebookApp.shutdown_no_activity_timeout = int(os.getenv('CULL_TIMEOUT'))

if os.getenv('CULL_KERNEL_TIMEOUT'):
    # shutdown kernels after no activity
    c.MappingKernelManager.cull_idle_timeout = int(os.getenv('CULL_KERNEL_TIMEOUT'))

if os.getenv('CULL_INTERVAL'):
    # check for idle kernels this often
    c.MappingKernelManager.cull_interval = int(os.getenv('CULL_INTERVAL'))

# a kernel with open connections but no activity still counts as idle
# this is what allows us to shutdown servers when people leave a notebook open and wander off
if os.getenv('CULL_CONNECTED') not in {'', '0'}:
    c.MappingKernelManager.cull_connected = True
