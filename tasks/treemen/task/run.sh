#!/bin/bash

set -euo pipefail

cd /treemen

flag="$1"
make main

echo "$flag" | ./main

bash redact.sh "$flag"
