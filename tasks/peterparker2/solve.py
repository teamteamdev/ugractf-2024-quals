import base64
from io import BytesIO
from PIL import Image
from pix2tex.cli import LatexOCR
import requests


TOKEN = "f4wqroe67xf3mq01"

model = LatexOCR()

def send(**kwargs):
    global state
    state = requests.post(f"https://peterparker2.q.2024.ugractf.ru/{TOKEN}/click", json=kwargs).json()

send()

while state["flag"] is None:
    print(state["counter"])
    if not state["need_captcha"]:
        send()
        continue

    im = Image.open(BytesIO(base64.b64decode(state["picture"].partition(",")[2])))
    s = model(im)
    print(s)
    s = (
        s
            .partition("=")[0]
            .replace("}{", ")/(")
            .replace("{", "(")
            .replace("}", ")")
            .replace("\\cdot", "*")
            .replace("\\left", "")
            .replace("\\right", "")
            .replace("\\frac", "")
            .replace("\\bigg", "")
    )
    try:
        value = eval(s)
    except Exception:
        print("oopsie")
        send()
        continue
    send(captcha_response=value)
