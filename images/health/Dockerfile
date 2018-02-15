# This image is to be build from the root to find requirements.txt, test files
# docker build -t <image-name> -f images/health/Dockerfile .
FROM python:3.6-alpine
# install requirements
RUN apk add --no-cache bash curl git openssh-client
ADD requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

# avoid prompt for github host key
RUN echo "StrictHostKeyChecking=no" >> /etc/ssh/ssh_config

# create and configure user
RUN adduser -S tester
USER tester
ENV HOME /home/tester
RUN git config --global user.name "Binder Health Checker" && \
    git config --global user.email "binder-health@checker.local"

# add tests to be run
ADD tests /srv/tests

# add and set entrypoint
ADD images/health/run-tests /usr/local/bin/run-tests
CMD run-tests
