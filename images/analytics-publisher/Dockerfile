# The build stage
# ---------------
FROM python:3.9-bullseye as build-stage

# Build wheels
#
# We set pip's cache directory and expose it across build stages via an
# ephemeral docker cache (--mount=type=cache,target=${PIP_CACHE_DIR}).
#
COPY requirements.txt requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    pip install build \
 && pip wheel \
        --wheel-dir=/tmp/wheels \
        -r requirements.txt

# Download tini
#
RUN if [ "$(uname -m)" = x86_64 ]; then ARCH=amd64; fi; \
    if [ "$(uname -m)" = aarch64 ]; then ARCH=arm64; fi; \
    curl -sSLo /tini "https://github.com/krallin/tini/releases/download/v0.19.0/tini-$ARCH" \
 && chmod +x /tini


# The final stage
# ---------------
FROM python:3.9-slim-bullseye
ENV PYTHONUNBUFFERED=1

# fix known vulnerabilities
RUN apt-get -y update \
 && apt-get -y upgrade \
 && rm -rvf /var/lib/apt/lists/*

# install wheels built in the build-stage
COPY requirements.txt /tmp/requirements.txt
ARG PIP_CACHE_DIR=/tmp/pip-cache
RUN --mount=type=cache,target=${PIP_CACHE_DIR} \
    --mount=type=cache,from=build-stage,source=/tmp/wheels,target=/tmp/wheels \
    pip install \
        --find-links=/tmp/wheels \
        -r /tmp/requirements.txt

COPY --from=build-stage /tini /tini

# copy content to container
WORKDIR /srv
COPY . .

ENTRYPOINT ["/tini", "--"]
CMD ["python", "/srv/run.py"]
