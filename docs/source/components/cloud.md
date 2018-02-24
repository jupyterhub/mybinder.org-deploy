# Cloud products

mybinder.org runs on [Google Cloud](https://cloud.google.com/) currently.
This document lists the various cloud products we use, and how we use them.

## Philosophy

We use **only** commodity cloud products - things that can be easily
replicated in other clouds *and* bare-metal hardware. This gives us
several technical and social advantages:

1. We avoid vendor lock-in, and can migrate providers if need be
   for any reason easily.
2. Makes sure our infrastructure is easily reproducible by others,
   who might have different resources available to them. This is 
   much harder if we have a hard dependency on any single cloud-provider's
   products.
3. Most such commodity products are open source, or have binary
   compatible open source implementations available. This allows us
   to file and fix bugs in other Open Source Software for the benefit
   of everyone, rather than just a particular cloud provider's implementation.
4. Local testing when a core component depends on a cloud provider's
   product is usually very difficult. Constraining ourselves to commodity
   products only makes this easier.

As an example, using PostgreSQL via [Google Cloud SQL](https://cloud.google.com/sql/docs/)
would be fine since anyone can run PostgreSQL. But using something like 
[Google Cloud Spanner](https://cloud.google.com/spanner/) or 
[Google Cloud PubSub](https://cloud.google.com/pubsub/docs/) is something to be
avoidded, since these can not be run without also being on Google Cloud.
Similarly, using [Google Cloud LoadBalancing](https://cloud.google.com/load-balancing/)
is also perfectly fine, since a lot of open source solutions (HAProxy, Envoy, nginx, etc)
can be used to provide the same service.

## Projects

We have two major [projects](https://cloud.google.com/storage/docs/projects)
that run on Google Cloud.

1. `binder-prod`, runs production - `mybinder.org` and all resources
   needed for it.
2. `binder-staging` runs staging - `staging.mybinder.org` and all resources
   needed for it.

We try to make staging and prod be as similar as possible. Staging should just
be smaller and use fewer resources. So everything we describe below
are present in staging too.

## Google Kubernetes Engine

The open source [Kubernetes](https://kubernetes.io/) project is used to run
all our code. [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine/)
is the google hosted version of Kubernetes. It is very close to what is shipped
as Open Source, and does not have much in the way of proprietary enhancements.

### Cluster

In production, the cluster is called `prod-a`. In staging, it is called `staging`.

### Node Pools

GKE has the concept of a [NodePool](https://cloud.google.com/kubernetes-engine/docs/concepts/node-pools)
that specifies the kind of machine (RAM, CPU, Storage) we want to use for our Kubernetes
cluster. If we want to change the kind of machines, we can create a new NodePool,
cordon the current one, wait for all pods in current nodes to die, and then delete the
current NodePool.

### Machine sizes

The `prod-a` cluster currently uses `n1-highmem-32` machines. These have
32 CPU cores and 208 GB of Memory. We use the `highmem` machines (with more Memory per CPU)
than `standard` machines for the following reasons:

1. Memory is an *incompressible* resource - once you give a process memory, you can
   not take it away without killing the process. CPU is *compressible* - you can
   take away how much CPU a process is using without killing it.
2. Our users generally seem to be running not-very-cpu-intensive code, as can be
   witnessed from our generally low CPU usage.
3. Docker layer caching gives us massive performance boosts - less time spent
   pulling images leads to faster startup times for users. Using larger nodes
   increases the cache hit rate, so we use nodes with more rather than less RAM.

Using `highmem` machines saves us a lot of money, since we are not paying for CPU
we are not using!

The `staging` cluster uses much smaller machines than the production one, to keep costs
down.

### Boot disk sizes

In `prod-a`, we use 1000 GB SSD disks as boot disks. On Google Cloud, the size of
the disk [controls](https://cloud.google.com/compute/docs/disks/performance) the
performance - larger the disk, faster it is. Our disks need to be fast since we
are doing a lot of IO operations during docker build / push / pull / run, so we
use SSDs.

Note that SSD boot disks are *not* a feature available on GKE to all customers -
we have been given [early access](https://github.com/kubernetes/kubernetes/issues/36499)
to this feature, since it makes a dramatic difference to our performance (and
we knew where to ask!).

Staging does not use SSD boot disks.

### Autoscaling

We use the GKE [Cluster Autoscaler](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler)
feature to add more nodes when we run out of resources. When the cluster is 100%
full, the cluster autoscaler adds a new node to handle more pods. However,
there is no way to make the autoscaler kick in at 80% of 90% utilization
([bug](https://github.com/kubernetes/autoscaler/issues/148)), so this leads
to [launch failures](https://github.com/jupyterhub/mybinder.org-deploy/issues/474)
for a while when a new node comes up.

The autoscaler can be set to have a `minimum` number of nodes and a `maximum` number
of nodes. 

## Google Container Registry

A core part of MyBinder.org is building, storing and then running docker images
(built by [repo2docker](https://github.com/jupyter/repo2docker)). Docker images
are generally stored in a [docker registry](https://github.com/docker/distribution),
using a well defined standard API. 

We use Google Cloud's hosted docker registry - [Google Container Registry (GCR)](https://cloud.google.com/container-registry/).
This lets us use a standard mechanism for storing and retrieving docker images
without having to run any of that infrastructure ourselves.


### Authentication

GCR is private by default, and can be only used from inside the Google Cloud project
the registry is located in. When using GKE, the authentication for pulling images
to run is already set up for us, so we do not need to do anything special. For pushing
images, we authenticate via a [service account](https://cloud.google.com/container-registry/docs/advanced-authentication#using_a_json_key_file).
You can find this service account credential under `registry` in `secrets/config/prod.yaml`
and `secrets/config/staging.yaml`.

### Access

The images are scoped per-project, the images made by `mybinder.org` are 
stored in the `binder-prod` project, and the images made by `staging.mybinder.org` 
are stored in the `binder-staging` project.

We do not allow users to pull our images, for a few reasons:

1. We pay network egress costs when images are used outside the project they are in,
   and this can become very costly!
2. This can be abused to treat us as a content redistributor - build
   an image with content you want, and then just pull the image from elsewhere. This
   makes us a convenient possible hop in cybercrime / piracy / other operations, 
   complicates possible [DMCA](https://en.wikipedia.org/wiki/Digital_Millennium_Copyright_Act) 
   / [GDPR](https://en.wikipedia.org/wiki/General_Data_Protection_Regulation) compliance and 
   probably a bunch of other bad things we do not have the imagination to foresee. 
3. We might decide to clean up old images when we no longer need them, and this might 
   break other users who might depend on this.

For users who want access to a docker image similar to how it is built with Binder,
we recommend using [repo2docker](https://github.com/jupyter/repo2docker) to build
your own, and push it to a registry of your choice.

### Naming

Since building an image takes a long time, we would like to re-use images as much
as possible. If we have built an image once for a particular repository at a particular
commit, we want to not rebuild that image - just re-use it as much as possible. 
We generate an image name for each image we build that is uniquely derived from 
the name of the repository + the commit hash. This lets us check easily if 
the image has already been built, and if so, we can skip the building step.

The code for generating this image name from repository information is
in [binderhub's builder.py](https://github.com/jupyterhub/binderhub/blob/master/binderhub/builder.py),
under `_generate_build_name`.

Sometimes, we *do* want to invalidate all previously built images - for example,
when we do a major notebook version bump. This will cause all repositories to be
rebuilt the next time they are launched. There is a performance cost to this, so
this invalidation has to be done judiciously. This is done by giving all the images
a `prefix` (`binderhub.registry.prefix` in `config/prod.yaml` and `config/staging.yaml`).
Changing this prefix will invalidate all existing images.

## Logging 

We use [Google Stackdriver](https://cloud.google.com/stackdriver/) for logging.
Stackdriver supports other features (such as metrics and dashboarding), but we 
use [prometheus](metrics.html) and [grafana](dashboards.html) instead for those
features. 