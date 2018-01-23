
# 2018-01-11, Warning from letsencrypt about outdated SSL certificate

## Summary

A team member received a warning from letsencrypt saying that the SSL certificate
for `beta.mybinder.org` was going to expire soon. This was unexpected because
we use `kube-lego` to automatically register new SSL certificates for various
sub-domains of `mybinder.org`. After a few days, we re-checked the SSL
certificate on `beta.mybinder.org` and it seemed to have renewed properly,
so this was a noop from our perspective. However it revealed a few things we
should do differently to make sure this doesn't happen again.

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

### 2018-01-19 11:00

We received another email saying that both `beta` and `docs` were out
of date.

Upon looking at the Google Analytics history, we realized that the date
these certificates were scheduled to run out was exactly 3 months from the
day we switched `mybinder.org` to point to the `beta` deployment.

The `letsencrypt` [expiration emails doc](https://letsencrypt.org/docs/expiration-emails/)
says that if the name / details of the certificate you request change at all,
you may receive these emails even though you've successfully renewed your certificate.

We double checked that the cert for `beta`, `docs`, and `*` look correct, which they did.

So, we concluded that we're getting these notices because the SSL details
changed and letsencrypt has (expectedly) failed to link the two.

### 2018-01-19 11:00

A team member noticed that this is because our kubernetes deployment has an
account that's unique to the domain we were using. So when we changed domains
(from `beta` to `*`), we also switched accounts on letsencrypt. Our old account
is what is triggering the emails, but our new account is working fine.

## Action items

### Process

- Do not use a single team member's email address for letsencrypt
- Instead, use a shared google groups email account so we all get pinged
  * This has been done: binder-team@googlegroups.com
- keep an eye on the SSL once the first expiration date comes around and make sure
  this is a correct assumption.

## Related Issues / PRs

https://github.com/jupyterhub/mybinder.org-deploy/issues/283
