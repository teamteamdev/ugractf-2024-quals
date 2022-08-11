from kyzylborda_lib.sandbox import start_oneshot
from kyzylborda_lib.secrets import get_flag, validate_token
from kyzylborda_lib.server import tcp


FLAG_SUBSTITUTE = b"\xb5\x04\x02\xe6\x8c\xc8\x62\x27\x8c\xc1\x70\x49\x15\xa8\x9d\x9d\x1f\x5b\x2a\x6f\xef\x6e\x01\xe7\xbc\xa6\xe5\x88\x0b\xbc\x9e\x9a\x75\x80\x5b\x78\x7a\x84\xae\x64\xe0\xef\x03\xe5\xb4\x1e\x81\x88\x7f\x06\x21\x35\xc1\x70\xff\x80\x12"


@tcp.listen
async def handle(conn: tcp.Connection):
    await conn.writeall(b"Enter token: ")
    token = (await conn.readline()).decode(errors="ignore").strip()
    if not validate_token(token):
        await conn.writeall(b"Wrong token\n")
        return
    flag = get_flag(token)
    assert len(flag) == len(FLAG_SUBSTITUTE)
    oneshot = await start_oneshot(token)
    with oneshot.open("/check_flag", "r+b") as f:
        f.seek(f.read().index(FLAG_SUBSTITUTE))
        f.write(flag.encode())
    return oneshot
