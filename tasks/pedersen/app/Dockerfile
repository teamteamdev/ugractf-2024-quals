FROM lukemathwalker/cargo-chef:0.1.62-rust-1.75-slim-bullseye as chef

WORKDIR /app

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder 
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json
COPY . .
RUN cargo build --release

FROM debian:bullseye-slim

WORKDIR /app
COPY --from=builder /app/target/release/backend /app/backend
COPY Rocket.toml /app/Rocket.toml
COPY static /app/static
COPY start.sh /app/start.sh

ENV SECRET_PATH /data

ENTRYPOINT ["/app/start.sh"]
