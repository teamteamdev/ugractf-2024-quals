import urllib.request, PIL.Image, io, equation, json, sys

def click(j={}):
    data = json.loads(urllib.request.urlopen(urllib.request.Request('https://peterparker2.q.2024.ugractf.ru/f4wqroe67xf3mq01/click', json.dumps(j).encode('ascii'), headers={'Content-Type': 'application/json'})).read().decode())
    if data['need_captcha']:
        assert data['picture'].startswith('data:')
        raw_pic = urllib.request.urlopen(data['picture']).read()
        with open(sys.argv[1], 'wb') as file:
            file.write(raw_pic)
        pic = PIL.Image.open(io.BytesIO(raw_pic)).convert('L')
        expr = equation.parse_image(pic)
        print(expr)
        value = equation.safe_eval(expr)
        print(value)
        j['captcha_response'] = value
    else:
        try: j['captcha_response']
        except KeyError: pass
    print(data['counter'], 'clicks left')

while True:
    click()
