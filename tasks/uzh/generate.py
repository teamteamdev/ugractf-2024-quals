#!/usr/bin/env python3

import codecs
import hmac
import json
import os
import random
import sys

SECRET0 = b"during course screen away"
PREFIX1 = "ugra_send_via_infrared_"
PREFIX2 = "ugra_it_gets_longer_"
SECRET1 = b"fur love look angry"
SECRET2 = b"comfortable coach aid weigh"
SALT2_SIZE = 6


def get_user_tokens():
    user_id = sys.argv[1]

    token = str(int(hmac.new(SECRET0, str(user_id).encode(), "sha1").hexdigest(), 16) % 1000000).zfill(6)
    flag1 = PREFIX1 + hmac.new(SECRET1, token.encode(), "sha256").hexdigest()[:SALT2_SIZE]
    flag2 = PREFIX2 + hmac.new(SECRET2, token.encode(), "sha256").hexdigest()[:SALT2_SIZE]

    return token, flag1, flag2


def generate():
    if len(sys.argv) < 3:
        print("Usage: generate.py user_id target_dir", file=sys.stderr)
        sys.exit(1)

    token, flag1, flag2 = get_user_tokens()

    json.dump({
        "uzh": {
            "flags": [flag1],
            "bullets": [token],
        },
        "uzh2": {
            "flags": [flag2],
            "bullets": [token],
        },
    }, sys.stdout)


if __name__ == "__main__":
    generate()
