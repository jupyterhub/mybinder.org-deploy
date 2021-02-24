#!/usr/bin/env python3
"""
Collect CIDR ip ranges from data centers

Generates inputs for network policies to ban ingress

`cidrs_:name()` returns a list of CIDRs for a datacenter owner

Currently only collecting ipv4 addresses
"""

import ipaddress
import os
from html.parser import HTMLParser

import requests
import yaml


def cidrs_aws():
    """AWS datacenters"""
    url = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    r = requests.get(url)
    r.raise_for_status()
 
    return [prefix["ip_prefix"] for prefix in r.json()["prefixes"]]


def cidrs_gcp():
    """Google Cloud datacenters"""
    url = "https://www.gstatic.com/ipranges/cloud.json"
    r = requests.get(url)
    r.raise_for_status()
    cidrs = []
    for record in r.json()["prefixes"]:
        if "ipv4Prefix" in record:
            cidrs.append(record["ipv4Prefix"])
        else:
            assert "ipv6Prefix" in record, f"Unexpected gcp record: {record}"
    return cidrs


class MicrosoftDownloadParser(HTMLParser):
    """Minimal HTML parser to find microsoft download links"""
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for attr, value in attrs:
                if attr.lower() == "href" and value.startswith(
                    "https://download.microsoft.com"
                ):
                    if value not in self.links:
                        self.links.append(value)


def cidrs_azure():
    """Azure data centers"""
    # leave it to microsoft to make this require a human confirmation dialog
    r = requests.get(
        "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519"
    )
    r.raise_for_status()
    link_finder = MicrosoftDownloadParser()
    link_finder.feed(r.text)
    links = link_finder.links
    if len(links) != 1:
        raise ValueError(f"Expected exactly one download link, got {links}")
    # example: https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_20210208.json
    download_url = links[0]
    r = requests.get(download_url)
    r.raise_for_status()
    # use a set because azure reports the same CIDRs many times
    cidrs = set()
    for record in r.json()["values"]:
        for cidr in record["properties"]["addressPrefixes"]:
            if ":" not in cidr:
                # exclude ipv6 cidrs that look like 2603:1040:a06:402::178/125
                cidrs.add(cidr)
    return cidrs


datacenters = {
    "aws": {
        "message": "AWS",
        "get_cidrs": cidrs_aws,
    },
    "gcp": {
        "message": "Google Cloud",
        "get_cidrs": cidrs_gcp,
    },
    "azure": {
        "message": "Azure",
        "get_cidrs": cidrs_azure,
    },
}


def generate_files():
    """Collect CIDRs and output them to consistent formats

    for consumption by our helm chart as network policies
    """
    config_common = os.path.join("config", "common")
    os.makedirs(config_common, exist_ok=True)

    for name, cfg in sorted(datacenters.items()):
        if name == "azure":
            # FIXME: skip azure until we work out
            # how to authorize test requests.
            # GitHub Actions run on Azure.
            continue

        message = cfg["message"]
        get_cidrs = cfg["get_cidrs"]
        # filter to unique values
        raw_cidrs = get_cidrs()
        print(f"Collected {len(raw_cidrs)} CIDRs for {message}")
        # Collapse overlapping CIDRs.
        # Azure in particular is reduced by a factor of 20 from 32k to ~1800
        # because of how they organize the data.
        # This also happens to ensure better sorting than lexicographical
        # sorting of strings (i.e. 3.4.5.6 comes before 123.4.5.6)
        networks = [ipaddress.ip_network(cidr) for cidr in raw_cidrs]
        cidrs = [str(net) for net in sorted(ipaddress.collapse_addresses(networks))]

        dest_file = os.path.join(config_common, f"datacenter-{name}.yaml")
        print(f"Writing {len(cidrs)} CIDRs to {dest_file}")
        ban_networks = {cidr: message for cidr in cidrs}
        with open(dest_file, "w") as f:
            yaml.dump(
                {
                    "binderhub": {
                        "config": {
                            "BinderHub": {
                                "ban_networks": ban_networks,
                            },
                        }
                    }
                },
                f,
            )


if __name__ == "__main__":
    generate_files()
