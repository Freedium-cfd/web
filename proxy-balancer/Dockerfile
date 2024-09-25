FROM haproxy:alpine3.20

USER root
RUN apk add --no-cache netcat-openbsd

USER haproxy

COPY haproxy/haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
