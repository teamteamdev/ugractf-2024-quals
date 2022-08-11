import os

from kyzylborda_lib.sandbox import start_oneshot
from kyzylborda_lib.secrets import get_flag, validate_token
from kyzylborda_lib.server import telnet


@telnet.listen
async def handle(conn: telnet.Connection):
    token = await conn.with_buffering(conn.get_user())
    if token is None:
        await conn.writeall(b"No token passed; use telnet -l <TOKEN> option\n")
        return
    if not validate_token(token):
        await conn.writeall(b"Wrong token\n")
        return

    oneshot = await start_oneshot(token, pty=True)
    with oneshot.open("/flag", "w") as f:
        f.write(get_flag(token) + "\n")
    # chown to root
    os.chown(oneshot.get_external_file_path("/flag"), 32768, 32768)
    os.chmod(oneshot.get_external_file_path("/flag"), 0o400)
    return oneshot
