import json
import os
import random

import tornado
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.ioloop import IOLoop
from tornado.log import enable_pretty_logging, app_log

from tornado.httpclient import AsyncHTTPClient
from tornado.web import RequestHandler


# Config for local testing
CONFIG = {
    "check": {"period": 5, "jitter": 0.1},
    "hosts": {
        "gke": dict(
            url="https://mybinder.org", weight=3, health="https://mybinder.org/versions"
        ),
        "ovh": dict(
            url="https://binder.mybinder.ovh",
            weight=1,
            health="https://binder.mybinder.ovh/versions",
        ),
    },
}

config_path = '/etc/federation-redirect/config.json'
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

    async def get(self):
        uri = self.request.uri

        host_name = self.get_cookie("host")
        # make sure the host is a valid choice and considered healthy
        if host_name not in self.host_names:
            host_name = random.choices(self.host_names, self.host_weights)[0]
        self.set_cookie("host", host_name, max_age=10)

        self.redirect(host_name + uri)


async def health_check(host, active_hosts):
    all_hosts = CONFIG["hosts"]
    app_log.info("Checking health of {}".format(host))

    client = AsyncHTTPClient()
    try:
        await client.fetch(all_hosts[host]["health"], request_timeout=2)

    # any kind of exception means the host is unhealthy
    except Exception:
        app_log.warning("{} is unhealthy".format(host))
        if host in active_hosts:
            active_hosts.pop(host)
            app_log.warning("{} has been removed from the rotation".format(host))

        # remove the host from the rotation for a while
        # and wait longer than usual to check it again
        jitter = CONFIG["check"]["jitter"] * (0.5 - random.random())
        IOLoop.current().call_later(
            2 * (1 + jitter) * CONFIG["check"]["period"],
            health_check,
            host,
            active_hosts,
        )

    else:
        if host not in active_hosts:
            active_hosts[host] = all_hosts[host]
            app_log.warning("{} has been added to the rotation".format(host))

        # schedule ourselves to check again later
        jitter = CONFIG["check"]["jitter"] * (0.5 - random.random())
        IOLoop.current().call_later(
            (1 + jitter) * CONFIG["check"]["period"], health_check, host, active_hosts
        )


def make_app():
    # we want a copy of the hosts config that we can use to keep state
    hosts = dict(CONFIG["hosts"])

    app = tornado.web.Application(
        [
            (r"/build/.*", RedirectHandler),
            (r"/v2/.*", RedirectHandler),
            (r"/repo/.*", RedirectHandler),
            (r"/", RedirectHandler),
        ],
        hosts=hosts,
        cookie_secret="get-me-dynamically",
        debug=True,
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
