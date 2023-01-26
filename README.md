# mybinder.org-deploy

Deployment: [![Build Status](https://github.com/jupyterhub/mybinder.org-deploy/workflows/Continuous%20Deployment/badge.svg)](https://github.com/jupyterhub/mybinder.org-deploy/actions)

Deployment, configuration, and Site Reliability documentation files for the
public [mybinder.org][] service.

---

Please note that this repository is participating in a study into sustainability
of open source projects. Data will be gathered about this repository for
approximately the next 12 months, starting from 2021-06-11.

Data collected will include number of contributors, number of PRs, time taken to
close/merge these PRs, and issues closed.

For more information, please visit
[our informational page](https://sustainable-open-science-and-software.github.io/) or download our [participant information sheet](https://sustainable-open-science-and-software.github.io/assets/PIS_sustainable_software.pdf).

---

#### Deploying a Binder Service other than mybinder.org

These files are specific to [mybinder.org][].
If you wish to deploy your own Binder instance, please **do not use** these files.
Instead, you should review the [BinderHub documentation][] and the
[`jupyterhub/binderhub`][] repo to set up your deployment.

## Site Reliability Guide [![Documentation Status](https://readthedocs.org/projects/mybinder-sre/badge/?version=latest)](https://mybinder-sre.readthedocs.io/en/latest/?badge=latest)

[Site Reliability Guide](https://mybinder-sre.readthedocs.io/en/latest/index.html), the collected wisdom of operating mybinder.org.

Amongst other things the guide contains:

- [How to do a deployment](https://mybinder-sre.readthedocs.io/en/latest/deployment/how.html)
- [What happens during a deployment?](https://mybinder-sre.readthedocs.io/en/latest/deployment/what.html)
- [Incident reports for past incidents](https://mybinder-sre.readthedocs.io/en/latest/incident-reports/incident_reports_toc.html)
- [Incident report template](https://github.com/jupyterhub/mybinder.org-deploy/blob/HEAD/docs/source/incident-reports/template-incident-report.md)

## Key Links

|                      | Staging                                                                                                                                                                                                                                  | Production                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Site                 | [staging.mybinder.org](https://staging.mybinder.org)                                                                                                                                                                                     | [mybinder.org](https://mybinder.org)                                                                            |
| CI Deployment        | [![Continuous Deployment](https://github.com/jupyterhub/mybinder.org-deploy/workflows/Continuous%20Deployment/badge.svg)](https://github.com/jupyterhub/mybinder.org-deploy/actions?query=workflow%3A%22Continuous+Deployment%22) (both) |
| Deployment checklist | staging                                                                                                                                                                                                                                  | prod                                                                                                            |
| Monitoring           | staging                                                                                                                                                                                                                                  | [prod](https://grafana.mybinder.org/dashboard/db/kubernetes-cluster-monitoring-binder-prod?refresh=60s&orgId=1) |

| Helm chart | dev                                                                             | stable                                                             |
| ---------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| JupyterHub | [dev](https://jupyterhub.github.io/helm-chart/#development-releases-jupyterhub) | [stable](https://jupyterhub.github.io/helm-chart/#stable-releases) |
| BinderHub  | [dev](https://jupyterhub.github.io/helm-chart/#development-releases-binderhub)  | -                                                                  |

[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
[binderhub documentation]: https://binderhub.readthedocs.io/en/latest/
