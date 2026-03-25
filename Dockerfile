# Dockerfile
#
# Minimal Alpine-based image for napihandler.
# Expects pre-built binaries to be present in the build context at:
#   dist/linux-amd64/napihandler   (linux/amd64 binary)
#   dist/linux-arm64/napihandler   (linux/arm64 binary)
#
# Built automatically by the GHA workflow for both linux/amd64 and linux/arm64
# and published to ghcr.io.

FROM alpine:latest

ARG TARGETARCH

COPY dist/linux-${TARGETARCH}/napihandler /usr/local/bin/napihandler

RUN chmod +x /usr/local/bin/napihandler

ENTRYPOINT ["/usr/local/bin/napihandler"]
