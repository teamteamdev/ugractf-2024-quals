#!/usr/bin/env python3

from kyzylborda_lib.secrets import get_flag, validate_token

import aiohttp.web
import aiohttp_jinja2 as jinja2
import base64
import gzip
from jinja2 import FileSystemLoader
import PIL.Image, PIL.ImageDraw, PIL.ImageFont, PIL.ImageOps
import io
import math
import os
import random
import sys


BASE_DIR = os.path.dirname(__file__)

MAX_ATTEMPTS = 9

DICTS = {c: gzip.decompress(open(os.path.join(BASE_DIR, f"dict-{c}.txt.gz"), "rb").read()).decode().strip().splitlines() for c in "if"}


# https://www.pythoninformer.com/python-libraries/pillow/imageops-deforming/
class WaveDeformer:
    def __init__(self):
        self._mapping = {i: i + random.random() * 10 for i in range(1680)}
        self._c1 = random.randint(22, 28)
        self._c2 = random.randint(13, 17)
        self._c3 = random.randint(55, 65)
        self._c4 = random.randint(48, 52)
        self._c5 = random.randint(27, 33)

    def transform(self, x, y):
        nx = self._mapping.get(x, x) + self._c1 * math.sin(x / self._c3)
        ny = self._mapping.get(y, y) + self._c2 * math.sin(x / self._c4 + y / self._c5)
        nx = max(0, min(nx, 1679))
        ny = max(0, min(ny, 399))
        return nx, ny

    def transform_rectangle(self, x0, y0, x1, y1):
        return (*self.transform(x0, y0),
                *self.transform(x0, y1),
                *self.transform(x1, y1),
                *self.transform(x1, y0),
                )

    def getmesh(self, img):
        self.w, self.h = img.size
        gridspace = 20

        target_grid = []
        for x in range(0, self.w, gridspace):
            for y in range(0, self.h, gridspace):
                target_grid.append((x, y, x + gridspace, y + gridspace))

        source_grid = [self.transform_rectangle(*rect) for rect in target_grid]

        return [t for t in zip(target_grid, source_grid)]



def make_app(state_dir):
    app = aiohttp.web.Application()
    routes = aiohttp.web.RouteTableDef()
    routes.static("/static", os.path.join(BASE_DIR, "static"))


    @routes.get("/{token}")
    async def slashless(request):
        return aiohttp.web.HTTPMovedPermanently(f"/{request.match_info['token']}/")


    @routes.get("/{token}/")
    async def main(request):
        if not validate_token(request.match_info["token"]):
            raise aiohttp.web.HTTPForbidden

        return jinja2.render_template("main.html", request, {"dicts": DICTS})


    @routes.post("/{token}/verify")
    async def verify(request):
        token = request.match_info["token"]
        if not validate_token(token):
            raise aiohttp.web.HTTPForbidden

        data = await request.post()

        fn = os.path.join(state_dir, token)
        with open(fn, "a") as f:
            f.write(f"{data.get('i')} {data.get('f')}\n")

        raise aiohttp.web.HTTPFound(f"/{token}/verify_result")


    @routes.get("/{token}/verify_result")
    async def verify_result(request):
        token = request.match_info["token"]
        if not validate_token(token):
            raise aiohttp.web.HTTPForbidden

        fn = os.path.join(state_dir, token)
        try:
            with open(fn) as f:
                attempts = f.read().rstrip("\n").splitlines()
        except FileNotFoundError:
            attempts = []

        if len(attempts) <= MAX_ATTEMPTS and ("inspektion fahrt" in attempts or "inspektionsfahrt " in attempts):
            img = PIL.Image.open(os.path.join(BASE_DIR, "flag.jpg"))
            draw = PIL.ImageDraw.Draw(img)

            font_b = PIL.ImageFont.truetype(os.path.join(BASE_DIR, "din.otf"), 72)
            font = PIL.ImageFont.truetype(os.path.join(BASE_DIR, "din.otf"), 48)
            
            draw.text((750, 50), "A C H T U N G !", (234, 0, 0), font=font_b)

            draw.text((750, 130), get_flag(token).replace("_from", "_\nfrom").replace("the_", "the_\n").replace("spalt_", "spalt_\n"), (0, 0, 0), font=font)

            img = PIL.ImageOps.deform(img, WaveDeformer(), resample=PIL.Image.BILINEAR)

            bio = io.BytesIO()
            img.save(bio, format="JPEG", quality=88)
            bio.seek(0)

            flag_img = base64.b64encode(bio.getvalue()).decode()
        else:
            flag_img = None

        return jinja2.render_template("main.html", request, {"attempts": max(0, MAX_ATTEMPTS - len(attempts)), "flag_img": flag_img})

    app.add_routes(routes)
    jinja2.setup(app, loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")))
    return app


if __name__ == "__main__":
    app = make_app(sys.argv[1])

    if os.environ.get("DEBUG") == "F":
        aiohttp.web.run_app(app, host="0.0.0.0", port=31337)
    else:
        aiohttp.web.run_app(app, path=os.path.join(sys.argv[1], "if.sock"))
