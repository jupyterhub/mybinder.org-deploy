from yaml import safe_load as load
import requests

print('Fetching the SHA for live BinderHub and repo2docker...')

# Load master requirements
url_requirements = "https://raw.githubusercontent.com/jupyterhub/mybinder.org-deploy/master/mybinder/requirements.yaml"
requirements = load(requests.get(url_requirements).text)
binderhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'binderhub'][0]
bhub_live = binderhub_dep['version'].split('-')[-1]

url_binderhub_requirements = "https://raw.githubusercontent.com/jupyterhub/binderhub/{}/helm-chart/binderhub/requirements.yaml".format(bhub_live)
requirements = load(requests.get(url_binderhub_requirements).text)
jupyterhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'jupyterhub'][0]
jhub_live = jupyterhub_dep['version'].split('-')[-1]

# Load master repo2docker
url_helm_chart = "https://raw.githubusercontent.com/jupyterhub/mybinder.org-deploy/master/mybinder/values.yaml"
helm_chart = requests.get(url_helm_chart)
helm_chart = load(helm_chart.text)
r2d_live = helm_chart['binderhub']['config']['BinderHub']['build_image'].split(':')[-1]

print('Fetching latest commit SHA for BinderHub and repo2docker...')

# Load latest r2d commit
url = "https://api.github.com/repos/jupyter/repo2docker/commits"
resp = requests.get(url)
r2d_master = resp.json()[0]['sha']

# Load latest binderhub and jupyterhub commits
repos = {'jupyterhub': 'zero-to-jupyterhub-k8s', 'binderhub': 'binderhub'}
latest_hash = {}
for i_repo, i_url in repos.items():
    url = "https://api.github.com/repos/jupyterhub/{}/commits".format(i_url)
    resp = requests.get(url)
    # Grab the *second to latest* commit since this will be the image SHA
    # The latest commit is the "merge" commit and is excluded.
    latest_hash[i_repo] = resp.json()[1]['sha']

url_bhub = 'https://github.com/jupyterhub/binderhub/compare/{}...{}'.format(bhub_live, latest_hash['binderhub'][:7])
url_r2d = 'https://github.com/jupyter/repo2docker/compare/{}...{}'.format(r2d_live, r2d_master[:7])
url_jhub = 'https://github.com/jupyterhub/zero-to-jupyterhub-k8s/compare/{}...{}'.format(jhub_live, latest_hash['jupyterhub'][:7])

print('---------------------\n')
print('BinderHub: {}'.format(url_bhub))
print('repo2docker: {}'.format(url_r2d))
print('JupyterHub: {}'.format(url_jhub))
print('\n---------------------')
