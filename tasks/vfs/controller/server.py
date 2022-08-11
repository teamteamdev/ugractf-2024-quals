from kyzylborda_lib.sandbox import start_oneshot
from kyzylborda_lib.secrets import validate_token
from kyzylborda_lib.server import tcp


@tcp.listen
async def handle(conn: tcp.Connection):
    await conn.writeall(b"Enter token: ")
    token = (await conn.readline()).decode(errors="ignore").strip()
    if not validate_token(token):
        await conn.writeall(b"Wrong token\n")
        return
    return await start_oneshot(token, pass_secrets=["flag"])
