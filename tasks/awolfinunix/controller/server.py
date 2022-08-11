import asyncio
from kyzylborda_lib.sandbox import start_oneshot, Volume
from kyzylborda_lib.secrets import get_flag, validate_token
import os
import tempfile
from quart import Quart, render_template, request


TIMEOUT = 10


PRELUDE = """#![forbid(unsafe_code)]
use std::cell::UnsafeCell;

fn main() {
    let flag = std::fs::read_to_string("flag").unwrap();
    std::fs::File::create("flag").unwrap();
    run(&UnsafeCell::new(flag));
}
"""


async def run_code(token, code):
    with tempfile.NamedTemporaryFile() as f_rust_code:
        with tempfile.NamedTemporaryFile() as f_flag:
            with tempfile.NamedTemporaryFile() as f_output:
                os.chmod(f_rust_code.name, 0o777)
                os.chmod(f_flag.name, 0o777)
                os.chmod(f_output.name, 0o777)
                f_rust_code.write((PRELUDE + code).encode())
                f_rust_code.flush()
                f_flag.write(get_flag(token).encode())
                f_flag.flush()
                box = await start_oneshot(
                    token,
                    volumes=[
                        Volume(f_rust_code.name, "/playground.rs", "ro"),
                        Volume(f_flag.name, "/flag", ""),
                        Volume(f_output.name, "/output", ""),
                    ],
                )
                try:
                    await asyncio.wait_for(box.wait(), TIMEOUT)
                    return f_output.read()
                except asyncio.TimeoutError:
                    await box.stop()
                    return "Time limit exceeded"


def make_app():
    app = Quart(__name__)

    @app.route("/<token>/", methods=["GET", "POST"])
    async def index(token):
        if not validate_token(token):
            return "Invalid token"

        if request.method == "GET":
            return await render_template("index.html")

        form = await request.form
        code = str(form["code"])
        return await run_code(token, code)

    return app
