import json
import os
import random
import sys

import tornado
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.gen import sleep
from tornado.ioloop import IOLoop
from tornado.log import enable_pretty_logging, app_log

from tornado.httpclient import AsyncHTTPClient, HTTPError, HTTPRequest
from tornado.httputil import HTTPHeaders
from tornado.web import RequestHandler


# Config for local testing
CONFIG = {
    "check": {"period": 10, "jitter": 0.1, "retries": 3, "timeout": 2},
    "hosts": {
        "gke": dict(
            url="https://gke.mybinder.org",
            weight=1,
            health="https://gke.mybinder.org/versions",
            prime=True,
        ),
        "ovh": dict(
            url="https://ovh.mybinder.org",
            weight=1,
            health="https://ovh.mybinder.org/versions",
            # health="https://httpbin.org/status/404",
        ),
    },
}

config_path = "/etc/federation-redirect/config.json"
if os.path.exists(config_path):
    app_log.info("Using config from '{}'.".format(config_path))
    with open(config_path) as f:
        CONFIG = json.load(f)
else:
    app_log.warning("Using default config!")


class ProxyHandler(RequestHandler):
    def initialize(self, host):
        self.host = host

    async def get(self):
        uri = self.request.uri

        target_url = self.host + uri

        headers = self.request.headers.copy()
        headers["Host"] = self.host[8:]

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
        if response.error and type(response.error) is not HTTPError:
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
    def prepare(self):
        # copy hosts config in case it changes while we are iterating over it
        hosts = dict(self.settings["hosts"])
        self.host_names = [c["url"] for c in hosts.values() if c["weight"] > 0]
        self.host_weights = [c["weight"] for c in hosts.values() if c["weight"] > 0]

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-control-allow-headers", "cache-control")

    async def get(self):
        uri = self.request.uri

        host_name = self.get_cookie("host")
        # make sure the host is a valid choice and considered healthy
        if host_name not in self.host_names:
            host_name = random.choices(self.host_names, self.host_weights)[0]
        self.set_cookie("host", host_name, path=uri)

        self.redirect(host_name + uri)


async def health_check(host, active_hosts):
    check_config = CONFIG["check"]
    all_hosts = CONFIG["hosts"]
    app_log.info("Checking health of {}".format(host))

    client = AsyncHTTPClient()
    try:
        for n in range(check_config["retries"]):
            try:
                await client.fetch(
                    all_hosts[host]["health"], request_timeout=check_config["timeout"]
                )
            except Exception:
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
                active_hosts.pop(host)
                app_log.warning(
                    "{} has been removed from the rotation ({})".format(host, str(e))
                )

        # remove the host from the rotation for a while
        # and wait longer than usual to check it again
        jitter = check_config["jitter"] * (0.5 - random.random())
        IOLoop.current().call_later(
            2 * (1 + jitter) * check_config["period"], health_check, host, active_hosts
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
            (r"/build/.*", RedirectHandler),
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
    enable_pretty_logging()

    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
