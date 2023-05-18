# https://github.com/terraform-aws-modules/terraform-aws-eks/blob/v18.26.6/docs/network_connectivity.md

resource "aws_security_group" "worker_group_all" {
  name_prefix = "worker_group_all_ports"
  vpc_id      = module.vpc.vpc_id


  ingress {
    protocol  = "-1"
    from_port = 0
    to_port   = 0
    self      = true
  }
  egress {
    protocol  = "-1"
    from_port = 0
    to_port   = 0
    # self      = true
    cidr_blocks = ["0.0.0.0/0"]
  }

}

resource "aws_security_group" "all_worker_mgmt" {
  name_prefix = "all_worker_management"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = [
      "10.0.0.0/8",
      "172.16.0.0/12",
      "192.168.0.0/16",
    ]
  }
}
