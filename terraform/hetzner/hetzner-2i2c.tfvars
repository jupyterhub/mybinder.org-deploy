state_s3_endpoint = "https://nbg1.your-objectstorage.com"
name              = "hetzner-2i2c"
registry_users    = ["hetzner-2i2c", "hetzner-gesis", "gesis-harbor"]
push_mirrors = {
  gesis = {
    name      = "gesis"
    url       = "https://registry.gesis.mybinder.org"
    access_id = "robot$mybinder-builds+2i2c-harbor-builder"
    # add secret via ui
  }
}
