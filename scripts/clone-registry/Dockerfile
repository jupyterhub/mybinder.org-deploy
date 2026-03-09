FROM quay.io/jupyterhub/k8s-binderhub:1.0.0-0.dev.git.3910.h9dd0c2cc
# RUN apt-get -y update && apt-get -y install skopeo
ADD --chmod=755 https://github.com/lework/skopeo-binary/releases/download/v1.22.0/skopeo-linux-amd64 /usr/local/bin/skopeo

RUN python3 -m pip install --no-cache tqdm
COPY policy.json /etc/containers/policy.json
COPY clone-registry.py /clone-registry.py
ENTRYPOINT ["tini", "--"]
CMD ["python3", "/clone-registry.py"]
