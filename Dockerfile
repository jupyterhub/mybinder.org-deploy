FROM alpine:3.6
RUN apk add --no-cache iproute2

ADD throttle /usr/local/bin/throttle
CMD ["/usr/local/bin/throttle"]
