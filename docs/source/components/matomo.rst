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
to the repo. A MySQL user with name ``matomo`` should also be created in
the Google Cloud Console.

Initial Installation
====================

Matomo is a PHP application, and this has a number of drawbacks. The initial
install **`must <https://github.com/matomo-org/matomo/issues/10257>`_** be completed
with a manual web interface. Matomo will error if it finds a complete ``config.ini.php``
file (which we provide) but no database tables exist.

The first time you install Matomo, you need to do the following:

1. Do a deploy. This sets up Matomo, but not the database tables
2. Use ``kubectl --namespace=<namespace> exec -it <matomo-pod> /bin/bash`` to
   get shell on the matomo container.
3. Run ``rm config/config.ini.php``.
4. Visit the web interface & complete installation. The database username & password
   are available in the secret encrypted files in this repo. So is the admin username
   and password. This creates the database tables.
5. When the setup is complete, delete the pod. This should bring up our ``config.ini.php``
   file, and everything should work normally.

This is not ideal.