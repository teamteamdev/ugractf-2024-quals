import json
import os.path
from pyanvil import BlockState, Material, World
import shutil

from kyzylborda_lib.generator import get_attachments_dir
from kyzylborda_lib.secrets import get_flag


def render_text(text: str) -> list[str]:
    with open("seven-plus.json") as f:
        font = json.load(f)

    lines = [""] * max(font["lineHeight"], max(glyph["offset"] + len(glyph["pixels"]) for glyph in font["glyphs"].values()))

    for c in text:
        glyph = font["glyphs"][c]
        for i in range(len(lines)):
            j = i - glyph["offset"]
            if 0 <= j < len(glyph["pixels"]):
                line = "".join("#" if c else " " for c in glyph["pixels"][j])
            else:
                line = " " * len(glyph["pixels"][0])
            lines[i] += line + " "

    while lines[-1].strip() == "":
        lines.pop()

    return lines


def generate():
    shutil.copytree("UgraCTF", "/tmp/UgraCTF")

    with World("/tmp/UgraCTF") as world:
        for y, line in enumerate(render_text(get_flag())):
            for x, c in enumerate(line):
                if c == "#":
                    world.get_block((x, 2, y)).set_state(BlockState(Material.pink_wool, {}))

    shutil.make_archive(os.path.join(get_attachments_dir(), "UgraCTF"), "zip", "/tmp/UgraCTF")
