# Terminology for the deployment

This page contains common words or phrases in the dev-ops community that will be useful in understanding and maintaining the `mybinder.org` deployment.

(term-cordoning)=
## "cordoning" a node

[Kubernetes page on cordoning](https://kubernetes.io/docs/concepts/architecture/nodes/#manual-node-administration).

Sometimes you want to ensure that **no new pods** will be started on a given node. Usually this is because you suspect the node has a problem with it, or you wish to remove the node but need it to be free of pods first.

Cordoning the node tells Kubernetes to make it **unschedulable**, which means new pods won\'t start on the node. It is common to wait several hours, then manually remove any remaining pods on the node before removing it manually.
