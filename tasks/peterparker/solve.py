import requests


TOKEN = "iafv8o68bzftwl2a"

def send(**kwargs):
    global state
    state = requests.post(f"https://peterparker.q.2024.ugractf.ru/{TOKEN}/click", json=kwargs).json()

send()

while state["flag"] is None:
    print(state["counter"])
    if not state["need_captcha"]:
        send()
        continue
    send(captcha_response=0)
