#!/usr/bin/env python3

from kyzylborda_lib.generator import get_attachments_dir
from kyzylborda_lib.secrets import get_flag


import os

XOR_KEY = [30, 137, 7, 51, 139, 125, 175, 150, 91, 114, 144, 138, 156, 120, 24, 121, 57, 249, 31, 215, 72,
           192, 136, 101, 110, 249, 222, 10, 253, 69, 66, 232, 106, 117, 146, 127, 222, 115, 133, 80, 20, 13,
           22, 106, 226, 204, 40, 190, 249, 207, 47, 31, 58, 162, 223, 23, 37, 158, 63, 115, 228, 75, 140, 92]

def generate():
    flag = get_flag()
    flag_enc = bytes([i ^ j for i, j in zip(flag.encode(), XOR_KEY)])

    data = open(os.path.join("private", "template.wasm"), "rb").read()
    with open(os.path.join(get_attachments_dir(), "flag.???"), "wb") as f:
        f.write(data.replace(b"X" * 64, flag_enc))


if __name__ == "__main__":
    generate()
