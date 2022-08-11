import asyncio
from kyzylborda_lib.secrets import get_flag, validate_token
from kyzylborda_lib.server import http
import sys
from urllib.parse import parse_qs


index = open("index.html").read()


@http.listen
async def handle(request: http.Request):
    token = request.path[1:]
    if not validate_token(token):
        return http.respond(404)

    if request.method == "POST":
        content_length = request.headers["Content-Length"]
        if content_length is None or len(content_length) > 10:
            return http.respond(400)
        content_length = int(content_length)
        if content_length > 4096:
            return http.respond(413)
        query = parse_qs(await request.data.read(content_length))
        prog = query.get(b"lisp", [b""])[0]
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "lisp.py",
            cwd="lisp",
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={"FLAG": get_flag(token)},
        )
        await proc.communicate(prog)

    return http.respond(200, index)
