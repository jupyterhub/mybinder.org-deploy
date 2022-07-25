# Federation Redirector

The **Federation Redirector** redirects incoming HTTP traffic to one of a
group of BinderHubs. It is used to implement a federation of hubs for
mybinder.org.

It is a Tornado web server that redirects traffic on a small set of predefined
endpoints to a randomly chosen hub, the redirect target.

The list of potential redirect targets is configured at start-up. Each target
consists of a hostname, a weighting factor and a URL to check the hubs health.
For each request a weighted random choice of all healthy targets is made and
the visitor is redirected there.

Periodically the redirector will `GET` the health check URL for a target. If
it returns an error (if `Docker registry` or `JupyterHub API` is unhealthy)
or the target is over its quota (`Pod quota`),
the target is removed from the list of healthy targets.
Unhealthy targets are checked less frequently but once they return to good
health they are automatically added back to the list of viable targets.

The redirect response contains a short lived cookie that is used to remember
the choice of target. This means that subsequent visits from the same user
agent will be directed to the same target.

## Running tests

To run the automated tests for the redirector change to this directory in
your terminal and run `pytest`. This should find the tests in
`test_rendezvous.py`.

## How to update requirements.txt

Because `pip-compile` resolves `requirements.txt` with the current Python for
the current platform, it should be run on the same Python version and platform
as our Dockerfile.

Note that as of 2022-05-30, `pip-compile` has issues with `pycurl`, but we
workaround them by by omitting the `-slim` part from the image in the command
below.

```shell
# run from images/federation-redirect
# update requirements.txt based on requirements.in
docker run --rm \
    --env=CUSTOM_COMPILE_COMMAND="see README.md" \
    --volume=$PWD:/io \
    --workdir=/io \
    --user=root \
    python:3.9-bullseye \
    sh -c 'pip install pip-tools==6.* && pip-compile --upgrade'
```
