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

## Installing `k3s`

We can use the [quickstart](https://docs.k3s.io/quick-start) on the `k3s` website, with the added
config of _disabling traefik_ that comes built in. We deploy nginx as part of our deployment, so we
do not need traefik.

1. Create a Kubelet Config file in `/etc/kubelet.yaml` so we can
   tweak various kubelet options, including maximum number of pods on a single
   node:

   ```yaml
   apiVersion: kubelet.config.k8s.io/v1beta1
   kind: KubeletConfiguration
   maxPods: 300
   ```

   We will need to develop better intuition for how many pods per node, but given we offer about
   450M of RAM per user, and RAM is the limiting factor (not CPU), let's roughly start with the
   following formula to determine this:

   maxPods = 1.75 * amount of ram in GB

   This adds a good amount of margin. We can tweak this later

2. Install `k3s`!

   ```bash
   curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="server --kubelet-arg=config=/etc/kubelet.yaml" sh -s - --disable=traefik
   ```

   This runs for a minute, but should set up latest `k3s` on that node! You can verify that by running
   `kubectl get node` and `kubectl version`.

## Extracting authentication information via a `KUBECONFIG` file

Follow https://docs.k3s.io/cluster-access#accessing-the-cluster-from-outside-with-kubectl

## Setup DNS entries

There's only one IP to set DNS entries for - the public IP of the VM. No loadbalancers or similar here.

mybinder.org's DNS is managed via Cloudflare. You should have access, or ask someone in the mybinder team who does!

Add the following entries:

- An `A` record for `X.mybinder.org` pointing to wards the public IP. `X` should be an organizational identifier that identifies and thanks whoever is donating this.
- Another `A` record for `*.X.mybinder.org` to the same public IP

Give this a few minutes because it may take a while to propagate.

## Make a config copy for this new member

TODO

## Make a secret config for this new member

TODO

## Deploy binder!

## Test and validate

## Add to the redirector
