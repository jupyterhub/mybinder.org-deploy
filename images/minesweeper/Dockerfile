# The build stage
# ---------------
FROM python:3.13-bookworm AS build-stage

RUN curl -sSLo /tini "https://github.com/krallin/tini/releases/download/v0.19.0/tini-amd64" \
 && chmod +x /tini

COPY requirements.txt requirements.txt
RUN pip wheel --wheel-dir /wheelhouse \
        -r requirements.txt


# The final stage
# ---------------
FROM python:3.13-slim-bookworm
ENV PYTHONUNBUFFERED=1

# fix known vulnerabilities
RUN apt-get -y update \
 && apt-get -y upgrade \
 && rm -rvf /var/lib/apt/lists/*

COPY --from=build-stage /tini /tini
COPY --from=build-stage /wheelhouse /wheelhouse
RUN pip install --no-cache-dir /wheelhouse/*.whl

ENTRYPOINT ["/tini", "--"]
# CMD/args is set via the Helm chart that also mounts the minesweeper script
