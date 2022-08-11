FROM rust:alpine AS builder
RUN rustup toolchain install nightly
COPY . .
RUN cargo +nightly build --release

FROM alpine:latest
COPY src src
COPY sticker.webp sticker.webp
COPY --from=builder target/release/vfs target/release/vfs
CMD ["target/release/vfs"]
