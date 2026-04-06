state_s3_endpoint = "https://nbg1.your-objectstorage.com"
name              = "hetzner-gesis"
registry_users    = ["hetzner-gesis", "2i2c-harbor"]
push_mirrors = {
  hetzner_2i2c = {
    name      = "2i2c"
    url       = "https://oci.2i2c.mybinder.org"
    access_id = "robot$mybinder-builds+gesis-harbor-builder"
    # access_secret in secrets/hetzner-gesis.tfvars
  }
  bids_ovh = {
    name      = "bids"
    url       = "https://registry.bids.mybinder.org"
    access_id = "robot$mybinder-builds+gesis-harbor-builder"
    # access_secret in secrets/hetzner-gesis.tfvars
  }
}
