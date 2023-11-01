# Enable NetworkPolicies on EKS

EKS automatically installs the VPC CNI plugin, but by default NetworkPolicies are not enabled.

1. Find the recommended version of the VPC CNI plugin
   https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html
2. Download the VPC-CNI Kubernetes manifest, replacing `1.15.0` with the recommended version
   ```
   curl -O https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/v1.15.0/config/master/aws-k8s-cni.yaml
   ```
3. Edit `aws-k8s-cni.yaml`:
   - Change all mentions of `us-west-2` to your region
   - Update the manifest following the `kubectl` instructions in
     https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html
     - Add `enable-network-policy-controller: "true"` to the `aws-node` ConfigMap
     - Set `--enable-network-policy=true` in the `aws-node` DaemonSet `aws-network-policy-agent` container
4. Apply:
   ```
   kubectl apply -f cni/aws-k8s-cni.yaml
   ```
