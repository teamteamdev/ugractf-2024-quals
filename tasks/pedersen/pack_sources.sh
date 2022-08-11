#!/bin/bash

mkdir -p public

cd app/
zip -r ../public/pedersen.zip src static Cargo.lock Cargo.toml rust-toolchain.toml
cd -
