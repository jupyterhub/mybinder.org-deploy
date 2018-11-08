FROM python:3.7-stretch

WORKDIR /srv

ADD . .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Python seems to never wanna flush to stdout without the '-u'
CMD ["python3", "-u", "/srv/run.py"]