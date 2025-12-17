"""
Get UUID for OVH flavor and image

OVH provider needs UUID,
but UI only presents name.
Need to use the API to produce a mapping.

# TODO: make the region a parameter
"""

from operator import itemgetter

import ovh

client = ovh.Client(endpoint="ovh-us")
service_name = "5e4c805d3c614a1085d7b7bc1fee46d6"
region = "US-EAST-VA-1"


print(f"{'FLAVOR':24} UUID")
for flavor in sorted(
    client.get(f"/cloud/project/{service_name}/flavor", region=region),
    key=itemgetter("name"),
):
    print(f"{flavor['name']:24} {flavor['id']}")

print(f"{'IMAGE':24} UUID")
for image in sorted(
    client.get(f"/cloud/project/{service_name}/image", osType="linux", region=region),
    key=itemgetter("name"),
):
    print(f"{image['name']:24} {image['id']}")
