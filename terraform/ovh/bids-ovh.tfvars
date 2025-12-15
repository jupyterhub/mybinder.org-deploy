
endpoint = "ovh-us"

service_name = "64010af5c9434a419fb16e53d92eb52b"
region       = "US-EAST-VA"
zone         = "US-EAST-VA-1"

name = "bids-ovh"
vm = {
  # flavor and image: see lookup_flavor_image.py
  flavor_id = "6f5e7aef-5e1d-47e4-ad85-8b235cc2bd00" # b3-64
  image_id  = "03302136-e20b-446e-8b27-cf0aaf161810" #"Ubuntu 24.04"
}
