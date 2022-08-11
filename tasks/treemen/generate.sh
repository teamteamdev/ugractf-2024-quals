#!/bin/bash
set -euo pipefail

secret='jlkfJKLflkdsjr3wnrm,32nfdsjl'

user_id="$1"
workdir="$2"

attachments_dir="$workdir/attachments"
mkdir -p $attachments_dir

flag_suffix=$(echo "$user_id" | openssl dgst -hmac "$secret" | cut -d' ' -f2)

flag="ugra_0fun_tr33_mem0ry_${flag_suffix:0:8}"
touch "$attachments_dir/talk"
opam init -y > /dev/null
opam exec -- bash /treemen/run.sh "$flag" > "$attachments_dir/talk"

cp /treemen/main.ml "$attachments_dir/main.ml"
cp /treemen/mem.c "$attachments_dir/mem.c"
zip "$attachments_dir/forest.zip" /treemen/dumps/* > /dev/null

echo "{\"flags\": [\"$flag\"]}"
