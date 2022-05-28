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
to the repo. A MySQL user with name ``matomo`` & a MySQL database with name ``matomo``
should also be created in the Google Cloud Console.

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

Admin access
============

The admin username for Matomo is ``admin``. You can find the password in
``secret/staging.yaml`` for staging & ``secret/prod.yaml`` for prod.

Security
========

PHP code is notoriously hard to secure. Matomo has had security audits,
so it's not the worst. However, we should treat it with suspicion &
wall off as much of it away as possible. Arbitrary code execution
vulnerabilities often happen in PHP, so we gotta use that as our
security model.

We currently have:

1. A firewall hole (in Google Cloud) allowing it access to the CloudSQL
   instance it needs to store data in. Only port 3307 (which is used by
   the OAuth2+ServiceAccount authenticated CloudSQLProxy) is open. This
   helps prevent random MySQL password grabbers from inside the cluster.
2. A Kubernetes NetworkPolicy is in place that limits what outbound
   connections Matomo can make. This should be further tightened down -
   ingress should only be allowed on the nginx port from our ingress
   controllers.
3. We do not mount a Kubernetes ServiceAccount in the Matomo pod. This
   denies it access to the KubernetesAPI.
