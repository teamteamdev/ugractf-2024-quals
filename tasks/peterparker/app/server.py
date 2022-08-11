import base64
from collections import defaultdict
from flask import Flask, render_template, request
from flask_babel import Babel
from kyzylborda_lib.secrets import get_flag, validate_token
from generator import generate_rendered


app = Flask(__name__)
babel = Babel(app, locale_selector=lambda: request.accept_languages.best_match(["ru", "en"]))

counter_by_token = defaultdict(lambda: 2024)
valid_captcha_response_by_token = defaultdict(lambda: float("nan"))

def get_common_state(token: str):
    counter = counter_by_token[token]
    return {
        "counter": counter,
        "flag": get_flag(token) if counter == 0 else None
    }


@app.route("/<token>/")
def index(token: str):
    if not validate_token(token):
        return "Invalid token."
    return render_template("index.html")

@app.route("/<token>/state")
def state(token: str):
    if not validate_token(token):
        return {"error": "Invalid token"}
    return get_common_state(token)

@app.route("/<token>/click", methods=["POST"])
def click(token: str):
    if not validate_token(token):
        return {"error": "Invalid token"}

    body = request.json

    if counter_by_token[token] == 0:
        return get_common_state(token) | {
            "need_captcha": False
        }

    if counter_by_token[token] % 10 != 0:
        counter_by_token[token] -= 1
        return get_common_state(token) | {
            "need_captcha": False
        }

    retry_captcha = False

    if "captcha_response" in body and isinstance(body["captcha_response"], (int, float)):
        success = abs(valid_captcha_response_by_token[token] - body["captcha_response"]) < 0.001
        if success:
            counter_by_token[token] -= 1
            valid_captcha_response_by_token[token] = float("nan")
            return get_common_state(token) | {
                "need_captcha": False
            }
        else:
            retry_captcha = True

    pix, valid_response = generate_rendered()
    valid_captcha_response_by_token[token] = valid_response
    return get_common_state(token) | {
        "need_captcha": True,
        "picture": "data:image/png;base64," + base64.b64encode(pix).decode(),
        "retry_captcha": retry_captcha
    }
