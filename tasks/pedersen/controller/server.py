from kyzylborda_lib.sandbox import start_box
from kyzylborda_lib.secrets import validate_token, get_flag, get_secret
from kyzylborda_lib.server import http


def init(box):
    with box.open("/data/flag.txt", "w") as f:
        f.write(get_flag(box.token))


@http.listen
async def handle(request: http.Request):
    token = request.path[1:].split("/")[0]
    if not validate_token(token):
        return http.respond(404)
    if "X-Forwarded-Host" in request.headers:
        del request.headers["Host"]
        request.headers["Host"] = request.headers["X-Forwarded-Host"]
    return await start_box(token, init=init)
