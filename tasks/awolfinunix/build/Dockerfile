FROM rust:latest
CMD ( rustc playground.rs && ./playground ) 2>&1 | head -c 8M >>output; echo "Exit code $?" >>output
