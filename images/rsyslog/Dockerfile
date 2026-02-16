# very simple minimal image with rsyslog
# for podLogs, forwarding pod logs to host syslog
FROM alpine:3.23
RUN apk add rsyslog rsyslog-omuxsock
CMD ["rsyslogd", "-n"]
