from pathlib import Path
from kyzylborda_lib.sandbox import start_box, stop_box
from kyzylborda_lib.secrets import get_flag, validate_token
from quart import Quart, render_template, request, redirect


app = Quart(__name__)


def validate_uid(uid):
    return uid in (2, 7)

async def get_box(token, uid):
    box = await start_box(token, f"uid{uid}")
    if uid == 2:
        with box.open("/root/flag.txt", "w") as f:
            f.write(get_flag(token) + "\n")
    return box


@app.route("/<token>/")
async def index(token: str):
    if not validate_token(token):
        return "Invalid token."
    if "Android" not in str(request.user_agent):
        return await render_template("android.html")
    return await render_template("index.html")

@app.route("/<token>/alarmui")
async def alarmui(token: str):
    if not validate_token(token):
        return "Invalid token."
    if "Android" not in str(request.user_agent):
        return await render_template("android.html")
    return await render_template("alarmui.html")

@app.route("/<token>/api/get-clocks", methods=["POST"])
async def get_clocks(token: str):
    if not validate_token(token):
        return "Invalid token"

    json = await request.json
    uid = json["uid"]

    if not validate_uid(uid):
        return {"error": "Invalid UID"}

    box = await get_box(token, uid)
    result = []
    with box.open("/etc/crontabs/alarm") as f:
        for line in f:
            result.append(" ".join(line.split()[:5]))
    return result

@app.route("/<token>/api/add-clock", methods=["POST"])
async def add_clock(token: str):
    if not validate_token(token):
        return "Invalid token"

    json = await request.json
    uid = json["uid"]
    pattern = json["pattern"]

    if not validate_uid(uid):
        return {"error": "Invalid UID"}

    box = await get_box(token, uid)
    with box.open("/etc/crontabs/alarm", "r") as f:
        crontab = f.read()
    clock_id = crontab.count("\n")
    crontab += f"{pattern} ring-alarm\n"
    with box.open("/etc/crontabs/alarm", "w") as f:
        f.write(crontab)
    Path(box.get_external_file_path("/etc/crontabs")).touch()
    return {"clockId": clock_id}

@app.route("/<token>/api/modify-clock", methods=["POST"])
async def modify_clock(token: str):
    if not validate_token(token):
        return "Invalid token"

    json = await request.json
    uid = json["uid"]
    clock_id = json["clockId"]
    new_pattern = json["newPattern"]

    if not validate_uid(uid):
        return {"error": "Invalid UID"}

    box = await get_box(token, uid)
    with box.open("/etc/crontabs/alarm", "r") as f:
        lines = f.read().splitlines(keepends=True)
    lines[clock_id] = f"{new_pattern} ring-alarm\n"
    with box.open("/etc/crontabs/alarm", "w") as f:
        f.write("".join(lines))
    Path(box.get_external_file_path("/etc/crontabs")).touch()
    return {"ok": True}


@app.route("/<token>/api/delete-clock", methods=["POST"])
async def delete_clock(token: str):
    if not validate_token(token):
        return "Invalid token"

    json = await request.json
    uid = json["uid"]
    clock_id = json["clockId"]

    if not validate_uid(uid):
        return {"error": "Invalid UID"}

    box = await get_box(token, uid)
    with box.open("/etc/crontabs/alarm", "r") as f:
        lines = f.read().splitlines(keepends=True)
    del lines[clock_id]
    with box.open("/etc/crontabs/alarm", "w") as f:
        f.write("".join(lines))
    Path(box.get_external_file_path("/etc/crontabs")).touch()
    return {"ok": True}


@app.route("/<token>/api/get-diagnostics", methods=["POST"])
async def get_diagnostics(token: str):
    if not validate_token(token):
        return "Invalid token"

    json = await request.json
    uid = json["uid"]

    if not validate_uid(uid):
        return {"error": "Invalid UID"}

    box = await get_box(token, uid)
    logs = "Fetching /home/alarm/logs from the device...\n"
    with box.open("/home/alarm/logs", "r") as f:
        logs += f.read()
    return {"logs": logs}

@app.route("/__internal__/reboot_container/<token>/", methods=["POST"])
async def reboot_container(token: str):
    if not validate_token(token):
        return "Invalid token"
    await stop_box(token)
    return redirect(request.query_string.decode(), code=303)
