FROM python:3.7-stretch

WORKDIR /srv

ADD . .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

CMD ["python3", "/srv/app.py"]
