#!/usr/bin/env python3

import hmac
import json
import sys

PREFIX = "ugra_localization_with_no_sanitazation_"
FLAG_SECRET = b"ODZkNTY0Y2UtZjFhYy00MDRkLTljNjQt"
SUFFIX_SIZE = 12
TOKEN_SECRET = b"MGNiNzUxMjAtZTdlMi00NzlkLWFhYmUt"
TOKEN_SIZE = 16

def get_user_tokens(user_id):
    token = hmac.new(TOKEN_SECRET, str(user_id).encode(), "sha256").hexdigest()[:TOKEN_SIZE]
    flag = PREFIX + hmac.new(FLAG_SECRET, token.encode(), "sha256").hexdigest()[:SUFFIX_SIZE]

    return token, flag

def generate():
    if len(sys.argv) < 3:
        print("Usage: generate.py user_id target_dir", file = sys.stderr)
        sys.exit(1)
    
    user_id = sys.argv[1]
    token, flag = get_user_tokens(user_id)

    json.dump({
        "flags": [flag],
        "urls": [f"https://worldwide.{{hostname}}/{token}/"]
    }, sys.stdout)

if __name__ == "__main__":
    generate()