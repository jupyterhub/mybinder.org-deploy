Site Reliability Guide for mybinder.org
=======================================

Introduction
------------

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
