ARG DIST=buster
# build in non-slim image, which has compilation dependencies
FROM python:3.9-$DIST as builder

# RUN apt-get -y update

COPY requirements.txt requirements.txt

RUN python3 -m pip wheel -r requirements.txt -w /wheelhouse

FROM python:3.9-slim-$DIST

# pycurl requires libcurl
RUN apt-get -y update \
 && apt-get -y install --no-install-recommends \
        libcurl4 \
 && apt-get clean \
 && rm -rvf /var/lib/apt/lists/*

COPY --from=builder /wheelhouse /wheelhouse
RUN python3 -m pip install /wheelhouse/*.whl

WORKDIR /srv
COPY app.py /srv/app.py

CMD ["python3", "/srv/app.py"]
