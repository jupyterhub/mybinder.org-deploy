FROM alpine:3.6
RUN apk add --no-cache iproute2

ADD tc-init /usr/local/bin/tc-init
CMD ["/usr/local/bin/tc-init"]
