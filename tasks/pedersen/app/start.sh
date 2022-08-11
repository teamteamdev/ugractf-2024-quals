#!/bin/sh

set -e

if [ ! -f /data/secret.txt ]; then
    head -c 32 /dev/urandom > /data/secret.txt
fi

exec /app/backend "$@"
