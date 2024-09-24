# How to deploy a change to notebooks.gesis.org?

[GESIS Leibniz Institute for the Social Sciences](https://www.gesis.org) is a member of the [mybinder.org federation](https://mybinder.readthedocs.io/en/latest/about/status.html). GESIS has on-premise servers and use it for the mybinder.org server. The use of on-premise servers requires a separate deployment because the access to the servers using SSH requires the tunelling using a VPN.

<!--
sequenceDiagram
    actor developer as Developer
    participant git as GitHub
    participant github-actions as GitHub Actions
    participant gesis-gitlab as GESIS GitLab
    participant gcp as Google Cloud
    participant gesis-notebooks as notebooks.gesis.org

    developer->>developer: git commit
    developer->>git: git push
    git->>github-actions: trigger
    github-actions->>github-actions: validation
    github-actions->>gcp: helm upgrade
    git->>gesis-gitlab: trigger
    gesis-gitlab->>gesis-gitlab: validation
    gesis-gitlab->>gesis-notebooks: helm upgrade
-->

![Sequence diagram illustrating the deployment.](./gesis-diagram.svg)

## Virtual Private Server configuration with Ansible

We use [Ansible](https://www.ansible.com/) to automate the configuration of the virtual private server (VPS) provided by GESIS. After a successful configuration, we will have a operational Kubernetes cluster to deploy mybinder.org.