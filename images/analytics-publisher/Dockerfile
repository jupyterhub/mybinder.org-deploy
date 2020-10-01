FROM python:3.8-slim-buster

WORKDIR /srv

COPY . .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Python seems to never wanna flush to stdout without the '-u'
CMD ["python3", "-u", "/srv/run.py"]
