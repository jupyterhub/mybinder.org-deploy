.. _matomo:

=================================
Matomo (formerly Piwik) analytics
=================================

`Matomo <https://matomo.org/>`_ is a self-hosted free &
open source alternative to `Google Analytics <https://analytics.google.com>`_.

Why?
====

Matomo gives us better control of what is tracked, how long it is stored
& what we can do with the data. We would like to collect as
little data as possible & share it with the world in safe ways
as much as possible. Matomo is an important step in making this possible.

How it is set up?
=================

Matomo is a PHP+MySQL application. We use the apache based upstream
`docker image <https://hub.docker.com/_/matomo/>`_ to run it. We can
improve performance in the future if we wish by switching to ``nginx+fpm``.

We use `Google CloudSQL for MySQL <https://cloud.google.com/sql/docs/mysql/>`_
to provision a fully managed, standard mysql database. The
`sidecar pattern <https://cloud.google.com/sql/docs/mysql/connect-kubernetes-engine>`_
is used to connect Matomo to this database. A service account with appropriate
credentials to connect to the database has been provisioned & checked-in
to the repo.