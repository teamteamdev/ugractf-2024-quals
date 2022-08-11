#!/usr/bin/env python3

from kyzylborda_lib.secrets import get_flag, validate_token

import aiohttp
import aiohttp.web
import aiohttp_jinja2 as jinja2
import datetime
from jinja2 import FileSystemLoader
import io
import json
import jwt
import os
import random
import re
import sys
import traceback


BASE_DIR = os.path.dirname(__file__)

RECAPTCHA_VERIFY_URL = "https://recaptchaenterprise.googleapis.com/v1/projects/ornate-fragment-378209/assessments?key=AIzaSyBiGqvrhFL-X3tPwDSZc-3CmaryV864i9c"
RECAPTCHA_VERIFY_DATA = lambda t: {"event": {"expectedAction": "REGISTER", "siteKey": "6Lco120pAAAAAH3JiaxFyNSwjksF9G3tLrriasEw", "token": t}}
JWT_SECRET = "aiwiBai7thigeiK3eingohbuiWai5Cae1it9iHueyais"

STAGES = {
    "user": ("ml581829106", ".*"),
    "password": ("qV*!2@x>Tp{", ".*"),
    "phone": ("+79688362090", "\\+79[0-9]{9}"),
    "confirmation": ("000000", "[0-9]{6}"),
    "card-ending": ("7524", "[0-9]{4}"),
    "passport-ending": ("0692", "[0-9]{4}"),
    "org": ("TeleTrade", "[A-Za-z0-9 ]+"),
    "country": ("India", "[A-Za-z]{3,}"),
    "card": ("5321304698557524", "[0-9]{16}"),
}


def lang(request):
    return "ru" if re.compile("\\bru\\b").search(request.headers.get("accept-language")) else "en"


def make_app(state_dir):
    app = aiohttp.web.Application()
    routes = aiohttp.web.RouteTableDef()


    @routes.get("/{token}")
    async def slashless(request):
        return aiohttp.web.HTTPMovedPermanently(f"/{request.match_info['token']}/")


    @routes.get("/{token}/")
    async def main(request):
        if not validate_token(request.match_info["token"]):
            raise aiohttp.web.HTTPForbidden

        new_cookie = jwt.encode({"user": None}, JWT_SECRET, algorithm="HS256")

        response = jinja2.render_template("main.html", request, {"lang": lang(request), "stage": "user", "regex": ".*"})
        response.set_cookie("state", new_cookie)
        return response


    @routes.post("/{token}/")
    async def main_post(request):
        token = request.match_info["token"]
        if not validate_token(token):
            raise aiohttp.web.HTTPForbidden

        data = await request.post()
        recaptcha_token = data.get("g-recaptcha-response")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(RECAPTCHA_VERIFY_URL, json=RECAPTCHA_VERIFY_DATA(recaptcha_token)) as resp:
                    is_valid = (await resp.json()).get("tokenProperties", {}).get("valid") or False
        except Exception:
            traceback.print_exc()
            is_valid = False

        if not is_valid:
            raise aiohttp.web.HTTPFound(f"/{token}/fail")

        state_cookie = request.cookies.get("state")
        try:
            cookie_data = jwt.decode(state_cookie, JWT_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            response = jinja2.render_template("main.html", request, {"lang": lang(request), "stage": "user"})
            response.del_cookie("state")
            return response

        value = data["input"]
        for k in cookie_data:
            if cookie_data[k] is None:
                stage = k
                if not re.compile(STAGES[k][1]).match(value):
                    status = "fail-format"
                elif value != STAGES[k][0]:
                    status = "fail-value"
                else:
                    status = None
                    cookie_data[k] = value
                    for kk in STAGES:
                        if kk not in cookie_data:
                            stage = kk
                            cookie_data[kk] = None
                            break
                    else:
                        cookie_data["login"] = "1"
                        stage = "login"

                with open(os.path.join(state_dir, token), "a") as f:
                    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f" {k} {status or 'ok'} - {value or ''}\n")

                break
        else:
            response = jinja2.render_template("main.html", request, {"lang": lang(request), "stage": "user"})
            response.del_cookie("state")
            return response

        new_cookie = jwt.encode(cookie_data, JWT_SECRET, algorithm="HS256")

        response = jinja2.render_template("main.html", request, {"lang": lang(request), "stage": stage,
                                                                 "regex": STAGES[stage][1] if stage in STAGES else None,
                                                                 "status": status, "value": value})
        response.set_cookie("state", new_cookie)
        return response


    @routes.get("/{token}/fail")
    async def fail(request):
        token = request.match_info["token"]
        if not validate_token(token):
            raise aiohttp.web.HTTPForbidden

        return jinja2.render_template("main.html", request, {"lang": lang(request), "fail": True}, status=400)


    @routes.get("/{token}/notifications")
    async def notifications(request):
        token = request.match_info["token"]
        if not validate_token(token):
            raise aiohttp.web.HTTPForbidden

        state_cookie = request.cookies.get("state")
        try:
            cookie_data = jwt.decode(state_cookie, JWT_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            response = jinja2.render_template("main.html", request, {"lang": lang(request)})
            response.del_cookie("state")
            return response

        flag = None
        if cookie_data.get("login"):
            flag = get_flag(token)
        
        return jinja2.render_template("main.html", request, {"lang": lang(request), "flag": flag}, status=200 if flag else 403) 


    app.add_routes(routes)
    jinja2.setup(app, loader=FileSystemLoader(os.path.join(BASE_DIR, "templates")))
    return app


if __name__ == "__main__":
    app = make_app(sys.argv[1])

    if os.environ.get("DEBUG") == "F":
        aiohttp.web.run_app(app, host="0.0.0.0", port=31337)
    else:
        aiohttp.web.run_app(app, path=os.path.join(sys.argv[1], "lookingsus.sock"))
