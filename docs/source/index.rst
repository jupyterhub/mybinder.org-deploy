Site Reliability Guide for mybinder.org
=======================================

What is the mybinder.org operations team?
-----------------------------------------

Behind the mybinder.org deployment is a team of contributors that
donate their time to keeping mybinder.org running smoothly. This
role is often called a
`Site Reliability Engineer <https://en.wikipedia.org/wiki/Site_Reliability_Engineering>`_.
(or SRE). We informally call this team the "mybinder.org operators".

This site is a collection of wisdom, tools, and other helpful information that the
mybinder.org operations team uses for maintenance and team-processes
around the BinderHub deployment at `mybinder.org <https://mybinder.org>`_.

**If you're interested in helping the mybinder.org operations team**, first
check out `this post on what an operator does <https://discourse.jupyter.org/t/the-operators-no-binder-isnt-forming-a-rock-band/694>`_.
If that still sounds interesting to you, please reach out to the operations team
via the `Jupyter Discourse <https://discourse.jupyter.org>`_.

Note that if you're not interested in information about the mybinder.org BinderHub deployment,
you may find more useful information elsewhere. If you're looking for the
Binder docs, `see this link <https://docs.mybinder.org>`_. If you're looking
for information on deploying your own BinderHub
`see this link <https://binderhub.readthedocs.io>`_.


Getting started
---------------

These resources describe how to get started with the mybinder.org operations
team. It contains checklists of steps to take to make sure you have the right
permissions, as well as contextual information about the mybinder.org deployment.

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   introduction.md
   getting_started.md
   production_environment.md
   terminology.md


Deployment and Operation
------------------------

Team processes as well as useful information about what you might
run into when maintaining mybinder.org.

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   deployment/prereqs.md
   deployment/how.md
   deployment/what.md

.. toctree::
    :maxdepth: 2
    :caption: Operation

    common_problems.md
    command_snippets.md


Components
----------

These pages describe the different technical pieces that make up the
mybinder.org deployment.

.. toctree::
   :maxdepth: 2

   components/metrics.md
   components/dashboards.md
   components/ingress.md
   components/cloud.md
   components/matomo.rst


Analytics
---------

A public events archive with data about daily Binder launches.

.. toctree::
   :maxdepth: 2

   analytics/events-archive

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
