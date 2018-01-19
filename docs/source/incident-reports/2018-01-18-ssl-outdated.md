
# 2018-01-18, Warning from letsencrypt about outdated SSL certificate

## Summary

A team member received a warning from letsencrypt saying that the SSL certificate
for `beta.mybinder.org` was going to expire soon. This was unexpected because
we use `kube-lego` to automatically register new SSL certificates for various
sub-domains of `mybinder.org`. After a few days, we re-checked the SSL
certificate on `beta.mybinder.org` and it seemed to have renewed properly,
so this was a noop from our perspective. However it revealed a few things we
should do differently to make sure this doesn't happen again.

## Related Issues / PRs

https://github.com/jupyterhub/mybinder.org-deploy/issues/283

## Timeline

All times in PST

### 2018-01-11

A team member received an email that our SSL for `beta.mybinder.org` was going to expire.
He opened https://github.com/jupyterhub/mybinder.org-deploy/issues/283.


### 2018-01-18

Another team member used the SSL certificate checking website below:

https://www.ssllabs.com/ssltest/analyze.html?d=beta.mybinder.org&latest

to inspect the current SSL certificate of `beta.mybinder.org`. This seemed
to be correctly renewed, and the immediate problem considered resolved.

## Action items

### Process

- Do not use a single team member's email address for letsencrypt
- Instead, use a shared google groups email account so we all get pinged
