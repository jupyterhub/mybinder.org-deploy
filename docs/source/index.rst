Site Reliability Guide for mybinder.org
=======================================

Introduction
------------

This site is a collection of wisdom, tools, and other helpful information to assist in
the maintenance and team-processes around the BinderHub deployment at `mybinder.org <https://mybinder.org>`_.
It's probably only relevant to you if you are an active maintainer of this deployment, though
feel free to browse this information if you think it is useful!

If you're looking for the Binder docs, `see this link <https://docs.mybinder.org>`_. If you're looking
for information on deploying your own BinderHub, `see this link <https://binderhub.readthedocs.io>`_.

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   getting_started.md
   production_environment.md
   terminology.md

Components
----------

.. toctree::
   :maxdepth: 2

   components/metrics.md
   components/dashboards.md
   components/ingress.md
   components/cloud.md
   components/matomo.rst

Deployment and Operation
------------------------

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   deployment_policy.md
   deployment/prereqs.md
   deployment/how.md
   deployment/what.md

.. toctree::
    :maxdepth: 2
    :caption: Operation

    common_problems.md
    command_snippets.md


Analytics
---------

.. toctree::
   :maxdepth: 2

   analytics/events-archive
   analytics/cloud-costs

Incident Reports
----------------

For more information on our guidelines and goals for incident reports, see
:ref:`incident-reporting`. Below is a list of incident reports in reverse
chronological order.

.. include:: incident_reporting.rst
   :start-after: (in reverse chronological order)

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
