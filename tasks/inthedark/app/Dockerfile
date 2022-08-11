FROM alpine:latest AS builder
RUN apk add --no-cache build-base
COPY check_flag.c /tmp/check_flag.c
RUN gcc /tmp/check_flag.c -o /tmp/check_flag -O2

FROM alpine:latest
COPY --from=builder --chmod=111 /tmp/check_flag /check_flag
RUN rm /*bin/*grep
USER 405
CMD ["/bin/sh", "-i"]
