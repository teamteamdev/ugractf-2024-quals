from flask import Flask, render_template, redirect, request, url_for, session, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from kyzylborda_lib.secrets import get_flag, validate_token
from flask_bootstrap import Bootstrap
from re import match
from flask_limiter import Limiter
from random import Random
from collections import deque

# def get_flag(token):
#     return "test-flag"

#def validate_token(token):
#     return True

def pin_by_token(token):
    random = Random(token)
    source = str(random.getrandbits(500)) # just to be sure
    code = ''
    i = 0
    while len(code) < 6:
        if source[i]  not in code:
            code += source[i]
        i += 1
    return code

def get_token_from_request():
    return request.path

def make_app():

    app = Flask(__name__)
    bootstrap = Bootstrap(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for = 1, x_host = 1)
    app.secret_key = 'MDQ1OGUxNTQtNjY2OC00ZjBkLTgwMGYt'
    limiter = Limiter(
        get_token_from_request,
        app=app,
        storage_uri="memcached://memcached:11211"
    )
    
    admin_username = 'herrpin1954'  
        
    @app.route("/favicon.ico")
    def favicon():
        return "404", 404
    
    @app.route("/<token>/")
    def index(token):
        if not validate_token(token):
            return "token error", 401
        else:
            return render_template("index.html", token=token)
        
    @app.route("/<token>/register", methods=['GET', 'POST'])
    @limiter.limit("1/second")
    def register(token):
        if not validate_token(token):
                return "token error", 401
        if request.method == 'GET':
            return render_template("register.html", token=token)
        if request.method == 'POST':
            admin_pin = pin_by_token(token)
            pin = request.form['pin']
            messages = validate_pin(pin, admin_pin)
            for message in messages:
                flash(message.upper())
            return render_template("register.html", token=token)
    
    @app.route("/<token>/login", methods=['GET', 'POST'])
    @limiter.limit("1/second")
    def login(token):
        if not validate_token(token):
            return "token error", 401
        if request.method == 'GET':
            return render_template("login.html", token=token)
        if request.method == 'POST':
            admin_pin = pin_by_token(token)
            username = request.form['username'].lower()
            pin = request.form.get('pin')
            if username == admin_username and pin == admin_pin:
                session['username'] = username
                return redirect(f"/{token}/flag")
            else:
                flash("НЕВЕРНЫЙ ПИН-КОД (НЕ ПОДХОДИТ)")
                return render_template("login.html", token=token)
        
    @app.route("/<token>/flag")
    def flag(token):
        if not validate_token(token):
            return "token error", 401
        if 'username' not in session:
            flash("НЕАВТОРИЗОВАННЫЙ ПОЛЬЗОВАТЕЛЬ (ПОПЫТКА НСД)")
            return redirect(url_for('login', token=token))
        return render_template("win.html", flag=get_flag(token))
    
    def validate_pin(pin, admin_pin):
        results = deque(maxlen=3)
        if not match(r'^[0-9]{6}$', pin):
            results.append("Пин-код должен содержать 6 цифр!")
            return results
        if admin_pin == pin:
            results.append(f"Этот код уже занят пользователем {admin_username}!")
            return results
        matches = {}
        for x1, d1 in enumerate(admin_pin):
            for x2, d2 in enumerate(pin):
                if d1 == d2:
                    matches[d1] = matches.get(d1, []) + [(x1, x2)]
        for digit, pos in matches.items():
            if len(pos) == 1 and pos[0][0] == pos[0][1]:
                results.append(
                    "Цифра {} на позиции {} уже используется 1 другим пользователем!".format(digit, pos[0][0])
                )
            elif len(pos) < 3:
                results.append(
                    "Цифра {} очень популярна и используется 1 другим пользователем!".format(digit)
                )
            else:
                results.append("В пин-коде слишком много одинаковых цифр!")
        results.append("В отделе учёта пользователей ведётся инвентаризация. Регистрация временно недоступна.")
        return results

    return app
