FROM alpine:latest
ARG TARGETARCH
COPY napihandler-${TARGETARCH} /usr/local/bin/napihandler
RUN chmod +x /usr/local/bin/napihandler
ENTRYPOINT ["/usr/local/bin/napihandler"]
