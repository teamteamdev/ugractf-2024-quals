from .attachments.verifier import Verifier, P
from collections import defaultdict
from kyzylborda_lib.secrets import get_flag, get_secret, validate_token
from kyzylborda_lib.server import http
import random
import time


last_op_by_token = defaultdict(lambda: 0)
verifier_by_token = defaultdict(Verifier)

@http.listen
async def handle(request: http.Request):
    components = request.path.strip("/").split("/")

    if len(components) == 1 and request.method == "GET":
        return http.respond(200, "This is a ZKP server. Please use prover.py to communicate with the backend.")

    if len(components) != 2 or request.method != "POST":
        return http.respond(400)

    token, command = components
    if not validate_token(token):
        return http.respond(404)

    if time.time() - last_op_by_token[token, command] < 10:
        return http.respond(429, "Please retry in 10 seconds.")
    last_op_by_token[token, command] = time.time()

    verifier = verifier_by_token[token]

    if command == "get-parameters":
        verifier.generate()
        return http.respond(200, ", ".join((hex(P), hex(verifier.g), hex(verifier.y))))
    elif command == "announce-cs":
        cs = [
            int.from_bytes(await request.data.readexactly(16384 // 8))
            for _ in range(len(verifier.choices))
        ]
        try:
            choices = verifier.prover_announces_cs(cs)
        except AssertionError:
            return http.respond(400)
        return http.respond(200, repr(choices))
    elif command == "answer-choices":
        answers = [
            int.from_bytes(await request.data.readexactly(16384 // 8))
            for _ in range(len(verifier.choices))
        ]
        try:
            choices = verifier.prover_answers_choices(answers)
        except AssertionError:
            return http.respond(403, "Wrong answer!")
        return http.respond(200, get_flag(token))

    return http.respond(404)
