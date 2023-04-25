.. _mybinder-federation:

===========================
The mybinder.org Federation
===========================

The current status of the mybinder.org federation can be found `here <https://mybinder.readthedocs.io/en/latest/about/status.html>`_.


Adding or removing a federation member
--------------------------------------

The following files contain references to the federation,
and should be updated when a federation member is added or removed:

#. pages for https://mybinder.readthedocs.io: `status <https://github.com/jupyterhub/mybinder.org-user-guide/blob/HEAD/doc/about/status.rst>`_ and `federation info <https://github.com/jupyterhub/mybinder.org-user-guide/blob/HEAD/doc/_data/support/federation.yml`_
#. `deployment to the cluster <https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/cd.yml>`_
#. `testing of the cluster configuration <https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/test-helm-template.yaml>`_
#. membership in `federationRedirect.hosts config for prod <https://github.com/jupyterhub/mybinder.org-deploy/blob/7aa58e033efe1ed1cee1b5cb7e789c1296deb36a/config/prod.yaml#L220>`_


Temporarily removing a federation member from rotation
------------------------------------------------------

There are a few reasons why you may wish to remove a Federation member from
rotation. For example, maintenance work, a problem with the deployment, and so
on.

There are 3 main files you may wish to edit in order to remove a cluster from the Federation:

#. *Required.* Set the ``binderhub.config.BinderHub.pod_quota`` key to ``0`` in the
   cluster's config file under the `config <https://github.com/jupyterhub/mybinder.org-deploy/tree/HEAD/config>`_
   directory
#. *Recommended.* Set the ``weight`` key for the cluster to ``0`` in the
   `helm chart values file <https://github.com/jupyterhub/mybinder.org-deploy/blob/7aa58e033efe1ed1cee1b5cb7e789c1296deb36a/config/prod.yaml#L220>`_
   in order to remove it from the redirector's pool
#. *Optional.* Comment out the cluster from the
   `continuous deployment <https://github.com/jupyterhub/mybinder.org-deploy/blob/4f42d791f92dcb3156e7c4ea92a236246bbf9135/.github/workflows/cd.yml#L168>`_
   file
