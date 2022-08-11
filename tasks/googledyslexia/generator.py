from kyzylborda_lib.secrets import get_flag


QWERTY_TO_DVORAK = str.maketrans("abcdefghijklmnopqrstuvwxyz_", "axje.uidchtnmbrl'poygk,qf;{")


def generate():
    return {
        "bullets": [
            get_flag().translate(QWERTY_TO_DVORAK)
        ]
    }
