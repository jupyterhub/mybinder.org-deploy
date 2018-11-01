FROM python:3.7-stretch

ADD . /srv

RUN python3 -m pip install --no-cache-dir -r /srv/requirements.txt

CMD ["python3", "/srv/event-archiver.py"]