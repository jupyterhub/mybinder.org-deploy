import json
import os
import random

import tornado
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.gen import sleep
from tornado.ioloop import IOLoop
from tornado.log import enable_pretty_logging, app_log

from tornado.httpclient import AsyncHTTPClient
from tornado.web import RequestHandler


# Config for local testing
CONFIG = {
    "check": {"period": 5, "jitter": 0.1, "retries": 3, "timeout": 2},
    "hosts": {
        "gke": dict(
            url="https://gke.mybinder.org",
            weight=3,
            health="https://gke.mybinder.org/versions",
            prime=True,
        ),
        "ovh": dict(
            url="https://ovh.mybinder.org",
            weight=1,
            health="https://ovh.mybinder.org/versions",
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


class RedirectHandler(RequestHandler):
    def prepare(self):
        # copy hosts config in case it changes while we are iterating over it
        hosts = dict(self.settings["hosts"])
        self.host_names = [c["url"] for c in hosts.values()]
        self.host_weights = [c["weight"] for c in hosts.values()]

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-control-allow-headers", "cache-control")

    async def get(self):
        uri = self.request.uri

        host_name = self.get_cookie("host")
        # make sure the host is a valid choice and considered healthy
        if host_name not in self.host_names:
            host_name = random.choices(self.host_names, self.host_weights)[0]
        self.set_cookie("host", host_name, max_age=10)

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
            if all_hosts[host]["prime"]:
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

    app = tornado.web.Application(
        [
            (r"/build/.*", RedirectHandler),
            (r"/v2/.*", RedirectHandler),
            (r"/repo/.*", RedirectHandler),
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
                {
                    "url": "https://gke.mybinder.org/assets/images/badge.svg",
                    "permanent": True,
                },
            ),
            (
                r"/about",
                tornado.web.RedirectHandler,
                {"url": "https://gke.mybinder.org/about", "permanent": True},
            ),
            (r"/", RedirectHandler),
            (r".*", RedirectHandler),
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
    enable_pretty_logging()

    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
