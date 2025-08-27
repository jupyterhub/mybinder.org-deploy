# Site Reliability Guide for `mybinder.org`

This site is a collection of wisdom, tools, and other helpful
information to assist in the maintenance and team-processes around the
[BinderHub] deployment at <https://mybinder.org>.

```{tip}
If you are looking for documentation on how to use <https://mybinder.org>, [see
the mybinder.org user documentation](https://docs.mybinder.org).
```

```{tip}
If you are looking for information on deploying your own BinderHub,
[see the BinderHub documentation][BinderHub].
```

## What is `mybinder.org`?

<https://mybinder.org> is a federation, named [the `mybinder.org` federation](mybinder-federation), of public deployments of [BinderHub].
<https://mybinder.org> acts as a proxy to computational resources donated by federation members.

## What is the `mybinder.org` operations team?

Behind the <https://mybinder.org> is a team of contributors that donate
their time to keeping <https://mybinder.org> running smoothly. This role is often
called a [Site Reliability
Engineer](https://en.wikipedia.org/wiki/Site_Reliability_Engineering)
(or SRE). We informally call this team the "`mybinder.org` operators".

**If you are interested in helping the `mybinder.org` operations team**,
first check out ["The Operators (no Binder isn’t forming a rock band)"](https://discourse.jupyter.org/t/the-operators-no-binder-isnt-forming-a-rock-band/694) on Jupyter instance of Discourse.
To show your interest in helping, please reach out to the operations
team via ["Interested in joining the mybinder.org operations team?"](https://discourse.jupyter.org/t/interested-in-joining-the-mybinder-org-operations-team/761) thread on Jupyter instance of Discourse.

```{toctree}
:maxdepth: 2
:caption: Guide
getting_started/index.md
deployment/index.rst
operation_guide/index.rst
components/index.rst
analytics/index.rst
incident-reports/index.rst
```

[BinderHub]: https://binderhub.readthedocs.io/