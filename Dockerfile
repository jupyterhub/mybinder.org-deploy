FROM python:3.6-alpine
ADD requirements.txt /tmp/requirements.txt
RUN pip install --no-cache -r /tmp/requirements.txt
ADD proxy-help /usr/local/bin/proxy-help
USER nobody
CMD /usr/local/bin/proxy-help
