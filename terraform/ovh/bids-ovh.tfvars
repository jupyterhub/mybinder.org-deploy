
endpoint = "ovh-us"

service_name = "64010af5c9434a419fb16e53d92eb52b"
region       = "US-EAST-VA"
zone         = "US-EAST-VA-1"

name = "bids-ovh"

registry_users = ["bids-ovh", "gesis-harbor"]

push_mirrors = {
  hetzner_2i2c = {
    name      = "2i2c"
    url       = "https://oci.2i2c.mybinder.org"
    access_id = "robot$mybinder-builds+bids-harbor-builder"
    # secret in secrets/bids-ovh.tfvars
  }
}
