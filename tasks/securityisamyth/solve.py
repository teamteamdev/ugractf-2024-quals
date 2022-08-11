import json
import random
import requests
from mt19937predictor import MT19937Predictor


BASE = "https://securityisamyth.q.2024.ugractf.ru"
TOKEN = "i80qhpqg7trg9dd0"



p, g, y = [int(n, 16) for n in requests.post(f"{BASE}/{TOKEN}/get-parameters").text.split(", ")]

predictor = MT19937Predictor()
predictor.setrandbits(g, 16384)
predictor.setrandbits(y, 16384)

choices = predictor.getrandbits(32)
choices = [(choices >> i) & 1 for i in range(32)]

print("Computing, please wait...")
cs = [pow(y, -1, p) if choice == 0 else 1 for choice in choices]
choices1 = eval(requests.post(f"{BASE}/{TOKEN}/announce-cs", data=b"".join(c.to_bytes(16384 // 8) for c in cs)).text)

answers = [0] * 32
result = requests.post(f"{BASE}/{TOKEN}/answer-choices", data=b"".join(answer.to_bytes(16384 // 8) for answer in answers)).text
print(result)
