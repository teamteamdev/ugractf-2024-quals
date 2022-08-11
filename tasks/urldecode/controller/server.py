import os
from tempfile import NamedTemporaryFile

from kyzylborda_lib.sandbox import start_oneshot, Volume
from kyzylborda_lib.secrets import validate_token, get_flag
from kyzylborda_lib.server import tcp


DUMMY_FLAG = "ugra_dummy_dummy_dummy_dummy_d_123456789012"

with open("/var/urldecode", "rb") as f:
    URLDECODE = f.read()

assert DUMMY_FLAG.encode() in URLDECODE


@tcp.listen
async def handle(conn: tcp.Connection):
    await conn.writeall(b"Enter token: ")
    token = (await conn.readline()).decode(errors="ignore").strip()
    if not validate_token(token):
        await conn.writeall(b"Wrong token\n")
        return
    with NamedTemporaryFile(delete_on_close=False) as f:
        f.write(URLDECODE.replace(DUMMY_FLAG.encode(), get_flag(token).encode()))
        f.close()
        os.chmod(f.name, 0o555)
        return await start_oneshot(token, volumes=[Volume(f.name, "/var/urldecode", "ro")])
