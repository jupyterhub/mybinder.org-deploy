=====================
Federation Redirector
=====================

The **Federation Redirector** redirects incoming HTTP traffic to one of a
group of BinderHubs. It is used to implement a federation of hubs for
mybinder.org.

It is a Tornado web server that redirects traffic on a small set of predefined
endpoints to a randomly chosen hub, the redirect target.

The list of potential redirect targets is configured at start-up. Each target
consists of a hostname, a weighting factor and a URL to check the hubs health.
For each request a weighted random choice of all healthy targets is made and
the visitor is redirected there.

Periodically the redirector will ``GET`` the health check URL for a target. If
it returns an error or any of services
(``Docker registry``, ``JupyterHub API`` and ``Pod quota``) is unhealthy,
the target is removed from the list of healthy targets.
Unhealthy targets are checked less frequently but once they return to good
health they are automatically added back to the list of viable targets.

The redirect response contains a short lived cookie that is used to remember
the choice of target. This means that subsequent visits from the same user
agent will be directed to the same target.
