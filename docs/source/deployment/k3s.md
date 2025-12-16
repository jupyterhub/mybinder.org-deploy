# Deploy a new mybinder.org federation member on a bare VM with `k3s`

[k3s](https://k3s.io/) is a popular kubernetes distribution that we can use
to build _single node_ kubernetes installations that satisfy the needs of the
mybinder project. By focusing on the simplest possible kubernetes installation,
we can get all the benefits of kubernetes (simplified deployment, cloud agnosticity,
unified tooling, etc) **except** autoscaling, and deploy **anywhere we can get a VM
with root access**. This is vastly simpler than managing an autoscaling kubernetes
cluster, and allows expansion of the mybinder federation in ways that would otherwise
be more difficult.

## VM requirements

The k3s project publishes [their requirements](https://docs.k3s.io/installation/requirements?),
but we have a slightly more opinionated list.

1. We must have full `root` access.
2. Runs latest Ubuntu LTS (currently 24.04). Debian is acceptable.
3. Direct internet access, inbound (public IP) and outbound.
4. "As big as possible", as we will be using all the capacity of this one VM
5. Ability to grant same access to the VM to all the operators of the mybinder federation.

## VM configuration

1. Allow clock synchronization based on [Network Time Protocol (NTP)](https://en.wikipedia.org/wiki/Network_Time_Protocol).

   The VM provider might have its own NTP server and enforce the use of it.

### Node setup on OVH

We have [OpenTofu](http://opentofu.org) configuration for deploying a new registry on OVH.
The cheapest way to deploy a node on OVH is via [VPS](https://www.ovhcloud.com/en/vps/).
A VPS-6 (24 core, 92GB RAM) with backups and an extra disk costs $90/month, whereas a _smaller_ b3-64 (16 core, 64GB) costs over $300.

Because we deploy harbor ourselves in the helm chart, tofu needs to be split in steps.

Steps:

1. setup k3s on the VM (steps below)
2. create a secret file like `secrets/ovh-creds.sh` with credentials for the OVH API
3. create an s3 bucket for terraform state in the OVH project
4. create an s3 user with access to the bucket
5. create a `.tfvars` file like `bids-ovh.tfvars` with the variables for the deployment.
   `service_name` is the UUID of the cloud project.
6. set `TF_CLI_ARGS=-var-file=my-file.tfvars`

Now you're ready to start deploying to OVH.
It's a little tricky because we can't deploy all at once, we have to:

1. deploy the s3 bucket for the registry:
   ```
   tofu apply -target=ovh_cloud_project_user_s3_policy.harbor
   ```
2. configure harbor s3 secrets in `secrets/config/${name}.yaml` from
   ```
   tofu output registry_s3
   ```
3. deploy via helm (`CI=1 python3 deploy.py ${name}`). (This is safe to do for `KUBECONFIG` clusters).
4. finally complete the terraform deployment configuring harbor with Tofu:
   ```
   tofu apply
   ```
5. Add registry account secrets into `secrets/config/${name}.yaml` from
   ```
   tofu output -show-sensitive
   ```

### Attaching a disk

If the VM has an additional disk for dind, it needs to be partitioned and mounted, [following this guide](https://help.ovhcloud.com/csm/en-gb-vps-config-additional-disk?id=kb_article_view&sysparm_article=KB0047555).
We made only the following changes:

- use `mkfs.xfs` instead of `mkfs.ext4`

This disk is where dind state should live, so set:

```yaml
binderhub:
  dind:
    hostLibDir: /mnt/disk/dind
```

to put dind state on the external disk.

## Installing `k3s`

We can use the [quickstart](https://docs.k3s.io/quick-start) on the `k3s` website, with the added
config of _disabling traefik_ that comes built in. We deploy nginx as part of our deployment, so we
do not need traefik.

1. Create a Kubelet Config file in `/etc/kubelet.yaml` so we can
   tweak various kubelet options, including maximum number of pods on a single node and when to cleanup unused images:

   ```yaml
   apiVersion: kubelet.config.k8s.io/v1beta1
   kind: KubeletConfiguration
   maxPods: 300
   # Clean up images pulled by kubernetes anytime we are over
   # 40% disk usage until we hit 20%
   imageGCHighThresholdPercent: 40
   imageGCLowThresholdPercent: 20
   ```

   We will need to develop better intuition for how many pods per node, but given we offer about
   450M of RAM per user, and RAM is the limiting factor (not CPU), let's roughly start with the
   following formula to determine this:

   maxPods = 1.75 \* amount of ram in GB

   This adds a good amount of margin. We can tweak this later

2. Install `k3s`!

   ```bash
   curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --kubelet-arg=config=/etc/kubelet.yaml" sh -s - --disable=traefik
   ```

   This runs for a minute, but should set up latest `k3s` on that node! You can verify that by running
   `kubectl get node` and `kubectl version`.

## Extracting authentication information via a `KUBECONFIG` file

Next, we extract the `KUBECONFIG` file that the `mybinder.org-deploy` repo and team members can use to access
this cluster externally by following [upstream documentation](https://docs.k3s.io/cluster-access#accessing-the-cluster-from-outside-with-kubectl).
The short version is:

1. Copy the `/etc/rancher/k3s/k3s.yaml` into the `secrets/` directory in this repo:

   ```bash
   scp root@<public-ip>:/etc/rancher/k3s/k3s.yaml secrets/<cluster-name>-kubeconfig.yml
   ```

   Pick a `<cluster-name>` that describes what cluster this is - we will be consistently using it for other files too.

   Note the `.yml` here - everything else is `.yaml`!

2. Change the `server` field under `clusters.0.cluster` from `https://127.0.0.1:6443` to `https://<public-ip>:6443`.

## Create a new ssh key for mybinder team members

For easy access to this node for mybinder team members, we create and check-in an ssh key as
a secret.

1. Run `ssh-keygen -t ed25519 -f secrets/<cluster-name>.key` to create the ssh key. Leave the passphrase blank.
2. Set appropriate permissions with `chmod 0400 secrets/<cluster-name>.key`.
3. Copy `secrets/<cluster-name>.key.pub` (**NOTE THE .pub**) and paste it as a **new line** in `/root/.ssh/authorized_keys` on your server. Do not replace any existing lines in this file.

## Setup DNS entries

There's only one IP to set DNS entries for - the public IP of the VM. No loadbalancers or similar here.

mybinder.org's DNS is managed via Cloudflare. You should have access, or ask someone in the mybinder team who does!

Add the following entries:

- An `A` record for `X.mybinder.org` pointing to wards the public IP. `X` should be an organizational identifier that identifies and thanks whoever is donating this.
- Another `A` record for `*.X.mybinder.org` to the same public IP

Give this a few minutes because it may take a while to propagate.

## Make a config + secret copy for this new member

Now we gotta start a config file and a secret config file for this new member. We can start off by copying an existing one!

Let's copy `config/hetzner-2i2c.yaml` to `config/<cluster-name>.yaml` and make changes!

1. Find all hostnames, and change them to point to the DNS entries you made in the previous step.
2. Change `ingress-nginx.controller.service.loadbalancerIP` to be the external public IP of your cluster
3. Adjust the following parameters based on the size of the server:
   a. `binderhub.config.LaunchQuota.total_quota`
   b. `dind.resources`
   c. `imageCleaner`
4. TODO: Something about the registry.

We also need a secrets file, so let's copy `secrets/config/hetzner-2i2c.yaml` to `secrets/config/<cluster-name>.yaml` and make changes!

1. Find all hostnames, and change them to point to the DNS entries you made in the previous step.
2. TODO: Something about the registry

## Deploy binder!

Let's tell `deploy.py` script that we have a new cluster by adding `<cluster-name>` to `KUBECONFIG_CLUSTERS` variable in `deploy.py`.

Once done, you can do a deployment with `./deploy.py <cluster-name>`! If it errors out, tweak and debug until it works.

## Test and validate

## Add to the redirector
