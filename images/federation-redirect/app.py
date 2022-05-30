import asyncio
import json
import math
import os
import random
import sys
from hashlib import blake2b

import prometheus_client
import tornado
import tornado.ioloop
import tornado.options
import tornado.web
from prometheus_client import Gauge
from tornado import options
from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from tornado.log import app_log
from tornado.web import RequestHandler

# Config for local testing
CONFIG = {
    "check": {
        "period": 10,
        "jitter": 0.1,
        "retries": 5,
        "timeout": 2,
        "failed_period": 300,
    },
    "load_balancer": "rendezvous",  # or "random"
    "pod_headroom": 10,  # number of available slots to consider a member 'available'
    "hosts": {
        "gke": dict(
            url="https://gke.mybinder.org",
            weight=100,
            health="https://gke.mybinder.org/health",
            versions="https://gke.mybinder.org/versions",
            prime=True,
        ),
        "ovh": dict(
            url="https://ovh.mybinder.org",
            weight=1,
            health="https://ovh.mybinder.org/health",
            # health="https://httpbin.org/status/404",
            versions="https://ovh.mybinder.org/versions",
        ),
        "gesis": dict(
            url="https://gesis.mybinder.org",
            weight=200,
            health="https://gesis.mybinder.org/health",
            versions="https://gesis.mybinder.org/versions",
        ),
    },
}


def get_config(config_path):
    app_log.info(f"Using config from '{config_path}'.")

    with open(config_path) as f:
        config = json.load(f)

    # merge default config
    config.setdefault("check", CONFIG["check"])
    for key in CONFIG["check"]:
        config["check"].setdefault(key, CONFIG["check"][key])

    for h in list(config["hosts"].keys()):
        # Remove empty entries from CONFIG["hosts"], these can happen because we
        # can't remove keys in our helm templates/config files. All we can do is
        # set them to Null/None. We need to turn the keys into a list so that we
        # can modify the dict while iterating over it
        if config["hosts"][h] is None:
            config["hosts"].pop(h)
        # remove trailing slashes in host urls
        # these can cause 404 after redirection (RedirectHandler) and we don't
        # realize it
        else:
            config["hosts"][h]["url"] = config["hosts"][h]["url"].rstrip("/")

    return config


CONFIG_PATH = "/etc/federation-redirect/config.json"
if os.path.exists(CONFIG_PATH):
    CONFIG = get_config(CONFIG_PATH)
else:
    app_log.warning("Using default config!")


class FailedCheck(Exception):
    """Exception class for health checks not being satisfied

    These checks are considered failures and not retried
    until the next interval.
    """

    def __init__(self, msg, reason):
        self.msg = msg
        self.reason = reason


def blake2b_hash_as_int(b):
    """Compute digest of the bytes `b` using the Blake2 hash function.
    Returns a unsigned 64bit integer.
    """
    return int.from_bytes(blake2b(b, digest_size=8).digest(), "big")


def rendezvous_rank(buckets, key):
    """Rank the buckets for a given key using Rendez-vous hashing

    Each bucket is scored for the specified key. The return value is a list of
    all buckets, sorted in decreasing order (highest ranked first).
    """
    ranking = []
    for (bucket, weight) in buckets:
        # The particular hash function doesn't matter a lot, as long as it is
        # one that maps the key to a fixed sized value and distributes the keys
        # uniformly across the output space
        hash = blake2b_hash_as_int(b"%s-%s" % (str(key).encode(), str(bucket).encode()))
        score = weight * (1.0 / -math.log(hash / 0xFFFFFFFFFFFFFFFF))
        ranking.append((score, bucket))

    return [b for (s, b) in sorted(ranking, reverse=True)]


def cache_key(uri):
    """Compute key for load balancing decisions"""
    key = uri.lower()

    if key.startswith("/build/gh"):
        # remove branch/tag/reference, all instances of a repo should have
        # the same key and hence target
        key = key.rsplit("/", maxsplit=1)[0]

    return key


# metrics

HEALTH = Gauge(
    "federation_health",
    "Overall health check status for each member: 1 = healthy, 0 = unhealthy."
    " 'member' is the federation member."
    " 'reason' is the check that failed, if unhealthy.",
    ["member", "reason"],
)

HEALTH_CHECK = Gauge(
    "federation_health_check",
    "Individual health check status for each member: 1 = healthy, 0 = unhealthy."
    " 'member' is the federation member."
    " 'check' is the name of the check.",
    ["member", "check"],
)

REDIRECTS = Gauge(
    "federation_redirect_count",
    "Number of requests routed to each member." " 'member' is the federation member.",
    ["member"],
)


class MetricsHandler(RequestHandler):
    async def get(self):
        self.set_header("Content-Type", prometheus_client.CONTENT_TYPE_LATEST)
        self.write(prometheus_client.generate_latest(prometheus_client.REGISTRY))


class ProxyHandler(RequestHandler):
    def initialize(self, host):
        self.host = host

    async def get(self):
        uri = self.request.uri

        target_url = self.host + uri

        headers = self.request.headers.copy()
        # don't override Host, which kubernetes uses for routing,
        # otherwise this will be an infinite loop proxying to ourself
        # Host will be set to the target Host by the request below.
        current_host = headers.pop("Host", None)
        if current_host:
            # set proxy host header
            headers.setdefault("X-Forwarded-Host", current_host)
            # preserve original Host in Origin so this looks like a cross-origin request
            # even though it's proxied
            headers["Origin"] = f"https://{current_host}"

        headers["X-Binder-Launch-Host"] = "https://mybinder.org/"

        body = self.request.body
        if not body:
            if self.request.method == "POST":
                body = b""
            else:
                body = None

        client = AsyncHTTPClient()

        req = HTTPRequest(target_url, method="GET", body=body, headers=headers)

        response = await client.fetch(req, raise_error=False)

        # For all non http errors...
        if response.error and not isinstance(response.error, HTTPError):
            self.set_status(500)
            self.write(str(response.error))
        else:
            self.set_status(response.code, response.reason)

            # clear tornado default header
            self._headers = HTTPHeaders()

            for header, v in response.headers.get_all():
                if header not in (
                    "Content-Length",
                    "Transfer-Encoding",
                    "Content-Encoding",
                    "Connection",
                ):
                    # some headers appear multiple times, eg 'Set-Cookie'
                    self.add_header(header, v)

            if response.body:
                self.write(response.body)


class RedirectHandler(RequestHandler):
    def initialize(self, load_balancer):
        self.load_balancer = load_balancer

    def prepare(self):
        # copy hosts config in case it changes while we are iterating over it
        hosts = dict(self.settings["hosts"])  # make a copy
        if not hosts:
            # no healthy hosts, allow routing to unhealthy 'prime' host only
            hosts = {
                key: host for key, host in CONFIG["hosts"].items() if host.get("prime")
            }
            app_log.warning(
                f"Using unhealthy prime host(s) {list(hosts)} because zero hosts are healthy"
            )
        self.hosts = hosts
        self.hosts_by_url = {}  # dict of {"https://gke.mybinder.org": "gke"}
        self.host_names = []  # ordered list of ["gke"]
        self.host_weights = []  # ordered list of numerical weights
        for name, host_cfg in hosts.items():
            if host_cfg["weight"] > 0:
                self.host_names.append(name)
                self.host_weights.append(host_cfg["weight"])
                self.hosts_by_url[host_cfg["url"]] = name

        # Combine hostnames and weights into one list
        self.names_and_weights = list(zip(self.host_names, self.host_weights))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-control-allow-headers", "cache-control")

    async def get(self):
        path = self.request.path
        uri = self.request.uri

        host_url = self.get_cookie("host")

        # make sure the host is a valid choice and considered healthy
        host_name = self.hosts_by_url.get(host_url)
        if host_name is None:
            if self.load_balancer == "rendezvous":
                host_name = rendezvous_rank(self.names_and_weights, cache_key(path))[0]
            # "random" is our default or fall-back
            else:
                host_name = random.choices(self.host_keys, self.host_weights)[0]
            host_url = self.hosts[host_name]["url"]

        REDIRECTS.labels(member=host_name).inc()
        self.set_cookie("host", host_url, path=path)

        # do we sometimes want to add this url param? Not for build urls, at least
        # redirect = url_concat(host_url + uri, {'binder_launch_host': 'https://mybinder.org/'})
        redirect = host_url + uri
        app_log.info(f"Redirecting {path} to {host_url}")
        self.redirect(redirect, status=307)


class ActiveHostsHandler(RequestHandler):
    """Serve information about active hosts"""

    def initialize(self, active_hosts):
        self.active_hosts = active_hosts

    async def get(self):
        self.write({"active_hosts": self.active_hosts})


async def health_check(host, active_hosts):
    check_config = CONFIG["check"]
    all_hosts = CONFIG["hosts"]
    app_log.info(f"Checking health of {host}")

    client = AsyncHTTPClient()
    try:
        for n in range(check_config["retries"]):
            try:
                # TODO we could use `asyncio.gather()` and fetch health and versions in parallel
                # raises an `HTTPError` if the request returned a non-200 response code
                # health url returns 503 if a (hard check) service is unhealthy

                # check versions
                # run this first, because it updates the prime version to check against,
                # and we don't want to skip that if the prime cluster is otherwise unhealthy
                response = await client.fetch(
                    all_hosts[host]["versions"], request_timeout=check_config["timeout"]
                )
                versions = json.loads(response.body)
                # if this is the prime host store the versions so we can compare to them later
                if all_hosts[host].get("prime", False):
                    old_versions = CONFIG.get("versions", None)
                    if old_versions != versions:
                        app_log.info(
                            f"Updating prime versions {old_versions}->{versions}"
                        )
                        CONFIG["versions"] = versions
                # check if this cluster is on the same versions as the prime
                # w/o information about the prime's version we allow each
                # cluster to be on its own versions
                if versions != CONFIG.get("versions", versions):
                    HEALTH_CHECK.labels(member=host, check="versions").set(0)
                    raise FailedCheck(
                        "{} has different versions ({}) than prime ({})".format(
                            host, versions, CONFIG["versions"]
                        ),
                        reason="versions",
                    )
                else:
                    HEALTH_CHECK.labels(member=host, check="versions").set(1)

                # check health
                response = await client.fetch(
                    all_hosts[host]["health"], request_timeout=check_config["timeout"]
                )
                health = json.loads(response.body)
                for check in health["checks"]:
                    HEALTH_CHECK.labels(member=host, check=check["service"]).set(
                        int(check["ok"])
                    )

                for check in health["checks"]:
                    if not check["ok"]:
                        raise FailedCheck(
                            f"{host} unhealthy: {check}", reason=check["service"]
                        )
                    if (
                        check["service"] == "Pod quota"
                        and check["quota"] is not None
                        and CONFIG["pod_headroom"]
                    ):
                        # apply headroom so we don't hit the hard pod limit after redirecting
                        if (
                            check["total_pods"] + CONFIG["pod_headroom"]
                            >= check["quota"]
                        ):
                            raise FailedCheck(
                                f"{host} is approaching pod quota: {check['total_pods']}/{check['quota']}",
                                reason=check["service"],
                            )

                        break
            except FailedCheck:
                # don't retry failures such as quotas/version checks
                # those aren't likely to change in 1s
                raise
            except Exception as e:
                # retry check on unhandled errors (e.g. connection failure)
                app_log.warning(
                    f"{host} health check failed, attempt {n + 1} of {check_config['retries']}: {e}"
                )
                # raise the exception on the last attempt
                if n + 1 == check_config["retries"]:
                    raise
                else:
                    await asyncio.sleep(1)

    # any kind of exception means the host is unhealthy
    except Exception as e:
        app_log.warning(f"{host} is unhealthy: {e}")
        if isinstance(e, FailedCheck):
            reason = e.reason
        else:
            reason = "unknown"
        HEALTH.labels(member=host, reason=reason).set(0)
        if host in active_hosts:
            # remove the host from the rotation for a while
            # prime hosts may still receive traffic when unhealthy
            # _if_ all other hosts are also unhealthy
            active_hosts.pop(host)
            app_log.warning(f"{host} has been removed from the rotation")

        # wait longer than usual to check unhealthy host again
        period = check_config["failed_period"]
    else:
        HEALTH.labels(member=host, reason="").set(1)
        if host not in active_hosts:
            active_hosts[host] = all_hosts[host]
            app_log.warning(f"{host} has been added to the rotation")
        period = check_config["period"]

    # schedule ourselves to check again later
    jitter = check_config["jitter"] * (0.5 - random.random())
    IOLoop.current().call_later((1 + jitter) * period, health_check, host, active_hosts)


def make_app():
    # we want a copy of the hosts config that we can use to keep state
    hosts = dict(CONFIG["hosts"])

    for host in hosts.values():
        if host.get("prime", False):
            prime_host = host["url"]
            break

    else:
        sys.exit("No prime host configured!")

    app = tornado.web.Application(
        [
            (r"/build/.*", RedirectHandler, {"load_balancer": CONFIG["load_balancer"]}),
            (
                r"/(badge\_logo\.svg)",
                tornado.web.RedirectHandler,
                {
                    "url": "https://static.mybinder.org/badge_logo.svg",
                    "permanent": True,
                },
            ),
            (
                r"/(badge\.svg)",
                tornado.web.RedirectHandler,
                {"url": "https://static.mybinder.org/badge.svg", "permanent": True},
            ),
            (
                r"/assets/(images/badge\.svg)",
                tornado.web.RedirectHandler,
                {"url": "https://static.mybinder.org/badge.svg", "permanent": True},
            ),
            (r"/active_hosts", ActiveHostsHandler, {"active_hosts": hosts}),
            (r"/metrics", MetricsHandler),
            (r".*", ProxyHandler, {"host": prime_host}),
        ],
        hosts=hosts,
        debug=False,
    )

    # start monitoring all our potential hosts
    for hostname in hosts:
        IOLoop.current().add_callback(health_check, hostname, hosts)

    return app


def main():
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    options.define("port", default=8080, help="port to listen on")
    options.parse_command_line()

    app = make_app()
    app.listen(options.options.port, xheaders=True)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
