#!/usr/bin/env python3

from kyzylborda_lib.generator import get_attachments_dir
from kyzylborda_lib.secrets import get_flag


import PIL.Image
import io
import random
import os


PATTERN = """
---U----R----*----N---
-S---GU---AE---S*---O-
---T----R----S----0---
----------------------
----------------------
----------------------
----------------------
----------------------
----------------------
------I-----R----P----
---W2----E4---*6----A-
-1-----3----5-----7---
----------------------
""".strip().split("\n")


def generate():
    flag = get_flag()
    random.seed(int(flag.replace("_", ""), 36))

    note_src_img = PIL.Image.open(os.path.join("private", "note.png"))
    note_img = note_src_img.copy()
   
    DX, DY = 9, 33
    W, H = 6, 9

    chars = {c: note_src_img.crop((DX + W * (n % len(PATTERN[0])), DY + H * (n // len(PATTERN[0])),
                                  DX + W * (n % len(PATTERN[0]) + 1), DY + H * (n // len(PATTERN[0]) + 1)))
             for n, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789*")}

    for y in range(len(PATTERN)):
        for x in range(len(PATTERN[0])):
            c = PATTERN[y][x]
            if c in '01234567':
                c = flag[-8:][int(c)]
            elif c == '-':
                c = random.choice(list(chars.keys()))
            note_img.paste(chars[c.upper()], (DX + W * x, DY + H * y))

    note_img = note_img.resize((note_img.size[0] * 2, note_img.size[1] * 2), PIL.Image.NEAREST)
    note_img.save(os.path.join(get_attachments_dir(), "your-note.png"))


if __name__ == "__main__":
    generate()

