import os

GRAFANA_SMTP_PWD = os.environ['GRAFANA_SMTP_PWD']
GRAFANA_SMTP_PWD = os.environ['GRAFANA_ADMIN_PWD']

with open('config/staging.yaml', 'r') as ff:
    text = ff.read()

text = text.replace('{{GRAFANA_SMPT_PWD}}', GRAFANA_SMTP_PWD)
text = text.replace('{{GRAFANA_ADMIN_PWD}}', GRAFANA_ADMIN_PWD)

with open('config/staging.yaml', 'w') as ff:
    ff.write(text)
