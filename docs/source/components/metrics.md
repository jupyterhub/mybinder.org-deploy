# Metrics collection with Prometheus

We collect operational metrics about all the components of mybinder.org
and create dashboards from them. This document details the components
involved in collecting, storing and querying the metrics.

This is only for operational metrics - **not** for analytics on repositories
built or traffic.

## Metrics Storage + Querying

We use [Prometheus](https://prometheus.io/) to store and query our metrics.

### What is Prometheus?

Prometheus is a [Time Series Database](https://en.wikipedia.org/wiki/Time_series_database)
optimized for storing operational metrics. It stores all data as 
streams of timestamped values belonging to the same **metric** and the 
same set of **labels**.

The **metric name** specifies the general feature of a system that is 
measured (e.g. `http_requests_total` - the total number of HTTP requests received). 

A set of labels for the same metric name identifies a particular 
dimensional instantiation of that metric (for example: all HTTP requests 
that used the method `POST` to the `/api/tracks` handler would be represented
as the time series `http_requests_total{method="POST", handler="/api/tracks"}`).

The prometheus documentation has more information on its 
[data model](https://prometheus.io/docs/concepts/data_model/) and the different
[kinds of time series](https://prometheus.io/docs/concepts/metric_types/) available.
These two pages are fairly short and are highly recommended reading!

### Querying

Prometheus has its own query language called 
[PromQL](https://prometheus.io/docs/prometheus/latest/querying/basics/),
optimized for time series queries. 

The prometheus documentation has fairly clear and thorough documentation
on PromQL - [basics](https://prometheus.io/docs/prometheus/latest/querying/basics/),
[operators](https://prometheus.io/docs/prometheus/latest/querying/operators/) 
and [functions](https://prometheus.io/docs/prometheus/latest/querying/functions/).
You do not need to become an expert, but a basic understanding is useful. 
There are also [examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
to pick up and play with!

[prometheus.mybinder.org](https://prometheus.mybinder.org) is our public
prometheus installation, and you can practice your queries there! 


### Metrics Ingestion

Prometheus uses a **pull** model for metrics. It has a list of 
targets, and constantly polls them for their current state, and
records what it gets back. The targets are supposed to respond
to these HTTP requests with data in the 
[prometheus format](https://prometheus.io/docs/instrumenting/exposition_formats/).

Our data is currently sourced from the following targets.

#### Node information

The [node_exporter](https://github.com/prometheus/node_exporter) exports
information about each node we run - CPU usage, memory left, disk space,
etc. It provides fairly detailed info, usually prefixed with `node_`. 
This is not kubernetes specific.

#### Kubernetes information

[kube-state-metrics](https://github.com/kubernetes/kube-state-metrics)
exposes information about the kubernetes cluster - such as number of pods
and the states they are in, number of nodes, etc. These are usually
prefixed with `kube_`.

These only contain information from kubernetes API itself. For example,
'how much RAM are these containers using' is not recorded by `kube-state-metrics`,
since that is not information that is available to the Kubernetes API. 
'how much RAM are these pods requesting' is, however, available.

#### Container information

[cadvisor](https://github.com/google/cadvisor) provides detailed runtime
information about all the containers running in the cluster. This is information
mostly not available from `kube-state-metrics` - such as 'how much RAM are
these containers using right now', etc. These are usually prefixed with
`container_`.

#### HTTP request information

We use the [nginx-ingress helm chart](https://github.com/kubernetes/charts/tree/master/stable/nginx-ingress)
to let all HTTP traffic into our cluster. This allows us to use
the [nginx VTS exporter](https://hnlq715.github.io/nginx-vts-exporter/)
to collect information in prometheus about requests / responses.
These metrics are prefixed with `nginx_`.

#### BinderHub information

[BinderHub](http://github.com/jupyterhub/binderhub) itself exposes
metrics about its operations in the prometheus format, using 
the [python prometheus client library](https://github.com/prometheus/client_python).
These are currently somewhat limited, and prefixed with `binderhub_`

### Configuration

Prometheus is installed using the 
[prometheus helm chart](https://github.com/kubernetes/charts/tree/master/stable/prometheus).
This installs the following components:

1. Prometheus server (storage + querying)
2. `node_exporter` on every node
3. A `kube-state-metrics` instance

`cadvisor` is already present on all nodes (it ships with the `kubelet`
kubernetes component), and the prometheus helm chart has configuration
that adds those as targets.

You can see the available options for configuring the prometheus
helm chart in its [values.yaml](https://github.com/kubernetes/charts/blob/master/stable/prometheus/values.yaml)
file. You can see the current configuration we have under the `prometheus`
section of `mybinder/values.yaml`, `config/prod.yaml` and `config/staging.yaml`.