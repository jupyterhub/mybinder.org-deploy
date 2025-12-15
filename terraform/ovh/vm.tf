data "local_file" "ssh_public_key" {
  # after creating the VM
  filename = "${path.module}/../../secrets/${var.name}.key.pub"
}

resource "ovh_cloud_project_ssh_key" "vm" {
  service_name = var.service_name
  name         = "${var.name}-ssh"
  public_key   = data.local_file.ssh_public_key.content
}

resource "ovh_cloud_project_instance" "vm" {
  service_name   = var.service_name
  region         = var.zone
  name           = "mybinder-${var.name}"
  billing_period = "hourly"
  boot_from {
    image_id = var.vm.image_id
  }
  flavor {
    flavor_id = var.vm.flavor_id
  }
  ssh_key {
    name = ovh_cloud_project_ssh_key.vm.name
  }
  network {
    public = true
  }

  auto_backup {
    cron     = "0 23 * * *"
    rotation = 7
  }
  # ignore image id update, which can change
  # and would require recreating the vm
  lifecycle {
    ignore_changes = [boot_from]
  }
}

output "vm_ip" {
  value = [
    for addr in ovh_cloud_project_instance.vm.addresses : addr.ip
  ]
}
