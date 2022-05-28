from yaml import safe_load as load
import requests

print('Fetching the SHA for live BinderHub and repo2docker...')

# Load master requirements
url_requirements = "https://raw.githubusercontent.com/jupyterhub/mybinder.org-deploy/master/mybinder/Chart.yaml"
requirements = load(requests.get(url_requirements).text)
binderhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'binderhub'][0]
bhub_live = binderhub_dep['version'].split('-')[-1]

url_binderhub_requirements = f"https://raw.githubusercontent.com/jupyterhub/binderhub/{bhub_live}/helm-chart/binderhub/requirements.yaml"
requirements = load(requests.get(url_binderhub_requirements).text)
jupyterhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'jupyterhub'][0]
jhub_live = jupyterhub_dep['version'].split('-')[-1]

# Load master repo2docker
url_helm_chart = "https://raw.githubusercontent.com/jupyterhub/mybinder.org-deploy/master/mybinder/values.yaml"
helm_chart = requests.get(url_helm_chart)
helm_chart = load(helm_chart.text)
r2d_live = helm_chart['binderhub']['config']['BinderHub']['build_image'].split(':')[-1]

print('Fetching latest commit SHA for BinderHub and repo2docker...')

# Load latest r2d commit from dockerhub
url = "https://hub.docker.com/v2/repositories/jupyter/repo2docker/tags/"
resp = requests.get(url)
r2d_master = resp.json()['results'][0]['name']

# Load latest binderhub and jupyterhub commits
url_helm_chart = 'https://raw.githubusercontent.com/jupyterhub/helm-chart/gh-pages/index.yaml'
helm_chart_yaml = load(requests.get(url_helm_chart).text)

latest_hash = {}
for repo in ['binderhub', 'jupyterhub']:
    updates_sorted = sorted(helm_chart_yaml['entries'][repo], key=lambda k: k['created'])
    latest_hash[repo] = updates_sorted[-1]['version'].split('-')[-1]

url_bhub = 'https://github.com/jupyterhub/binderhub/compare/{}...{}'.format(bhub_live, latest_hash['binderhub'])
url_r2d = f'https://github.com/jupyter/repo2docker/compare/{r2d_live}...{r2d_master[:8]}'
url_jhub = 'https://github.com/jupyterhub/zero-to-jupyterhub-k8s/compare/{}...{}'.format(jhub_live, latest_hash['jupyterhub'])

print('---------------------\n')
print(f'BinderHub: {url_bhub}')
print(f'repo2docker: {url_r2d}')
print(f'JupyterHub: {url_jhub}')
print('\n---------------------')
