# The build stage
# ---------------
FROM python:3.9-bullseye as build-stage

RUN curl -sSLo /tini "https://github.com/krallin/tini/releases/download/v0.19.0/tini-amd64" \
 && chmod +x /tini

COPY requirements.txt requirements.txt
RUN pip wheel --wheel-dir /wheelhouse \
        -r requirements.txt


# The final stage
# ---------------
FROM python:3.9-slim-bullseye
ENV PYTHONUNBUFFERED=1

# fix known vulnerabilities
RUN apt-get -y update \
 && apt-get -y upgrade \
 && apt-get -y install --no-install-recommends \
        # libcurl is required by pycurl
        libcurl4 \
 && rm -rvf /var/lib/apt/lists/*

COPY --from=build-stage /tini /tini
COPY --from=build-stage /wheelhouse /wheelhouse
RUN pip install --no-cache-dir /wheelhouse/*.whl

# copy content to container
WORKDIR /srv
COPY . .

ENTRYPOINT ["/tini", "--"]
CMD ["python", "/srv/app.py"]
