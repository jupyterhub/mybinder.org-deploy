from binderhub.repoproviders import FakeProvider

c.BinderHub.use_registry = False
c.BinderHub.builder_required = False
c.BinderHub.repo_providers = {'gh': FakeProvider}
c.BinderHub.tornado_settings.update({'fake_build':True})

c.BinderHub.about_message = ('<br /><p style="width: 650px; margin: 0px auto;">mybinder.org is public infrastructure operated by the <a href="https://jupyterhub-team-compass.readthedocs.io/en/latest/team.html#binder-team">Binder Project team</a>.<br /><br />'
                             'The Binder Project is a member of <a href="https://jupyter.org">Project Jupyter</a>, which is a fiscally '
                             'sponsored project of <a href="https://numfocus.org/">NumFocus</a>, a US 501c3 non-profit.<br /><br />'
                             'For abuse please email: <a href="mailto:binder-team@googlegroups.com">binder-team@googlegroups.com</a>, to report a '
                             'security vulnerability please see: <a href="https://mybinder.readthedocs.io/en/latest/faq.html#where-can-i-report-a-security-issue">Where can I report a security issue</a><br /><br />'
                             'For more information about the Binder Project, see <a href="https://docs.mybinder.org/about">the About Binder page</a></p>')
