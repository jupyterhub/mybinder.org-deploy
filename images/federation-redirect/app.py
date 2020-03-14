import json
import os
import random
import sys

from hashlib import blake2b

import tornado
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.gen import sleep
from tornado.ioloop import IOLoop
from tornado.log import app_log
from tornado import options

from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.httputil import HTTPHeaders, url_concat
from tornado.web import RequestHandler


# Config for local testing
CONFIG = {
    "check": {"period": 10, "jitter": 0.1, "retries": 5, "timeout": 2},
    "load_balancer": "rendezvous",  # or "random"
    "hosts": {
        "gke": dict(
            url="https://gke.mybinder.org",
            weight=1,
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
            weight=1,
            health="https://gesis.mybinder.org/health",
            versions="https://gesis.mybinder.org/versions",
        ),
    },
}


def get_config(config_path):
    app_log.info("Using config from '{}'.".format(config_path))

    with open(config_path) as f:
        config = json.load(f)

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
    for bucket in buckets:
        # The particular hash function doesn't matter a lot, as long as it is
        # one that maps the key to a fixed sized value and distributes the keys
        # uniformly across the output space
        score = blake2b_hash_as_int(
            b"%s-%s" % (str(key).encode(), str(bucket).encode())
        )
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


class ProxyHandler(RequestHandler):
    def initialize(self, host):
        self.host = host

    async def get(self):
        uri = self.request.uri

        target_url = self.host + uri

        headers = self.request.headers.copy()
        headers["Host"] = self.host[8:]
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
        hosts = dict(self.settings["hosts"])
        self.host_names = [c["url"] for c in hosts.values() if c["weight"] > 0]
        self.host_weights = [c["weight"] for c in hosts.values() if c["weight"] > 0]

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-control-allow-headers", "cache-control")

    async def get(self):
        path = self.request.path
        uri = self.request.uri

        host_name = self.get_cookie("host")
        # make sure the host is a valid choice and considered healthy
        if host_name not in self.host_names:
            if self.load_balancer == "rendezvous":
                host_name = rendezvous_rank(self.host_names, cache_key(path))[0]
            # "random" is our default or fall-back
            else:
                host_name = random.choices(self.host_names, self.host_weights)[0]

        self.set_cookie("host", host_name, path=path)

        # do we sometimes want to add this url param? Not for build urls, at least
        # redirect = url_concat(host_name + uri, {'binder_launch_host': 'https://mybinder.org/'})
        redirect = host_name + uri
        app_log.info('Redirecting {} to {}'.format(path, host_name))
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
    app_log.info("Checking health of {}".format(host))

    client = AsyncHTTPClient()
    try:
        for n in range(check_config["retries"]):
            try:
                # TODO we could use `asyncio.gather()` and fetch health and versions in parallel
                # raises an `HTTPError` if the request returned a non-200 response code
                # health url returns 503 if a (hard check) service is unhealthy
                response = await client.fetch(
                    all_hosts[host]["health"], request_timeout=check_config["timeout"]
                )
                health = json.loads(response.body)
                for check in health["checks"]:
                    # pod quota is a soft check
                    if check["service"] == "Pod quota":
                        if not check["ok"]:
                            raise Exception(
                                "{} is over its quota: {}".format(host, check)
                            )
                        break
                # check versions
                response = await client.fetch(
                    all_hosts[host]["versions"], request_timeout=check_config["timeout"]
                )
                versions = json.loads(response.body)
                # if this is the prime host store the versions so we can compare to them later
                if all_hosts[host].get("prime", False):
                    all_hosts["versions"] = versions
                # check if this cluster is on the same versions as the prime
                # w/o information about the prime's version we allow each
                # cluster to be on its own versions
                if versions != all_hosts.get("versions", versions):
                    raise Exception(
                        "{} has different versions ({}) than prime ({})".format(
                            host, versions, all_hosts["versions"]
                        )
                    )
            except Exception as e:
                app_log.warning(
                    "{} failed, attempt {} of {}".format(
                        host, n + 1, check_config["retries"]
                    )
                )
                # raise the exception on the last attempt
                if n == check_config["retries"] - 1:
                    raise
                else:
                    await sleep(1)

    # any kind of exception means the host is unhealthy
    except Exception as e:
        app_log.warning("{} is unhealthy".format(host))
        if host in active_hosts:
            # prime hosts are never removed, they always get traffic and users
            # will see what ever healthy or unhealthy state they are in
            # this protects us from the federation ending up with zero active
            # hosts because of a glitch somewhere in the health checks
            if all_hosts[host].get("prime", False):
                app_log.warning(
                    "{} has NOT been removed because it is a prime ({})".format(
                        host, str(e)
                    )
                )

            else:
                # remove the host from the rotation for a while
                active_hosts.pop(host)
                app_log.warning(
                    "{} has been removed from the rotation ({})".format(host, str(e))
                )

        # wait longer than usual to check unhealthy host again
        jitter = check_config["jitter"] * (0.5 - random.random())
        IOLoop.current().call_later(
            30 * (1 + jitter) * check_config["period"], health_check, host, active_hosts
        )

    else:
        if host not in active_hosts:
            active_hosts[host] = all_hosts[host]
            app_log.warning("{} has been added to the rotation".format(host))

        # schedule ourselves to check again later
        jitter = check_config["jitter"] * (0.5 - random.random())
        IOLoop.current().call_later(
            (1 + jitter) * check_config["period"], health_check, host, active_hosts
        )


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
            (r".*", ProxyHandler, {"host": prime_host}),
        ],
        hosts=hosts,
        cookie_secret="get-me-dynamically",
        debug=False,
    )

    # start monitoring all our potential hosts
    for hostname in hosts:
        IOLoop.current().call_later(
            CONFIG["check"]["period"], health_check, hostname, hosts
        )

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
