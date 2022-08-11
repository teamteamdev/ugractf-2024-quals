from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.middleware.proxy_fix import ProxyFix
from kyzylborda_lib.secrets import get_flag, validate_token
from flask_bootstrap import Bootstrap
from functools import lru_cache
from random import Random

@lru_cache(maxsize=100)
def generate_users(token):
    random = Random(token)
    offset = random.randint(0, 100000)
    n_users = random.randint(50, 100) + offset
    # format: 861[0-9]{7}
    users = {
            f'861{n:07d}': { 
                'isValid': bool(random.getrandbits(1)),
                'signedOnlineConsent': bool(random.getrandbits(1))
            } 
            for n in range(offset, n_users)
    }
    # ensure a valid user exists
    users[f'861{random.randint(0, n_users):07d}'] = {
            'isValid': True,
            'signedOnlineConsent': True
    }
    return users
    

def make_app():
    app = Flask(__name__)
    bootstrap = Bootstrap(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for = 1, x_host = 1)
    app.secret_key = 'MzkxNzRlYTEtYTAyOS00YWNiLTk3MmIt'
       
    @app.route("/favicon.ico")
    def favicon():
        return "404", 404
    
    @app.route("/<token>/")
    def index(token):
        if not validate_token(token):
            return "token error", 401
        else:
            return render_template("index.html", token=token)

    @app.route("/<token>/list_users")
    def get_users(token):
        if not validate_token(token):
            return "token error", 401
        return generate_users(token)
        
    @app.route("/<token>/login", methods=["GET", "POST"])
    def login(token):
        print('fff')
        if not validate_token(token):
            return "token error", 401
        if session.get('auth'):
            return redirect(url_for('index', token=token))
        else:
            if request.method == 'POST':
                if bilet := request.form.get('bilet'):
                    if user := generate_users(token).get(bilet):
                        if all(user.values()):
                            flash('Вы вошли в систему!')
                            session['auth'] = bilet
                            return render_template("index.html", token=token)
                    else:
                        flash('Недействительный номер читательского билета (возможно, вы не подписали Согласие на обработку персональных данных, обратитесь в библиотеку по адресу, указанному на Главной странице')
                else:
                    flash('Произошла системная ошибка')
            return render_template("login.html", token=token)

        
    @app.route("/<token>/logout")
    def logout(token):
        if not validate_token(token):
            return "token error", 401
        if session.get('auth'):
            session.pop('auth')
        return redirect(url_for('index', token=token))

    @app.route("/<token>/catalog")
    def catalog_page(token):
        # Просто в шаблоне отрендерить все буксы со ссылками на них (по индексу в массиве) прямо внутри шаблона
        if not validate_token(token):
            return "token error", 401
        if session.get('auth'):
            return render_template("catalog.html", token=token, books=BOOKS)
        else:
            return redirect(url_for('index', token=token))

    @app.route("/<token>/catalog/<int:book_id>", methods=['GET', 'POST'])
    def book_page(token, book_id):
        # может попозже помогу сверстать шаблон доступа к книге
        # 2 состояния: подать заявку
        # и заявка подана (т.е. форма провалидирована - тогда показывать флаг типа в номере заказ если книга нужная)
        if not validate_token(token):
            return "token error", 401
        if session.get('auth'):
            if not (book_id >= 0 and book_id < len(BOOKS)):
                flash('Запрашиваемая книга не найдена!')
                return redirect(url_for('catalog_page', token=token)) 

            if BOOKS[book_id]['phd'] or BOOKS[book_id]['driver']:
                if request.method == 'POST':
                    if request.form.get('vuz_id') and request.form.get('driver_id'):
                        flag = get_flag(token)
                        flash(f"Книга была успешно выписана! Для получения книги, предъявите следующий код при посещении библиотеки: {flag} ")
                        return render_template("book.html", token=token, book=BOOKS[book_id], form_trigger=False, out_of_stock=False)
                    else:
                        return render_template("book.html", token=token, book=BOOKS[book_id], form_trigger=True, out_of_stock=False)
                if request.method == 'GET':
                    return render_template("book.html", token=token, book=BOOKS[book_id], form_trigger=True, out_of_stock=False)             
            return render_template("book.html", token=token, book=BOOKS[book_id], form_trigger=False, out_of_stock=True)
        else:
            return redirect(url_for('index', token=token))
               
    return app


BOOKS = [
        # нагенерь 10-15 книжек чатгптой
        {
            'title': 'Маленький Принц',
            'author': 'А. Де-Сент Экзюпери',
            'driver': False,
            'phd': False,
            'description': 'Книга для детей и взрослых'
        },
        {
            'title': 'Идиот',
            'author': 'Федор Достоевский',
            'driver': False,
            'phd': False,
            'description': 'Роман о противоречиях русской души'
        },
        {
            'title': '1984',
            'author': 'Джордж Оруэлл',
            'driver': False,
            'phd': False,
            'description': 'Антиутопический роман о тоталитарном обществе'
        },
        {
            'title': 'Гарри Поттер и философский камень',
            'author': 'Джоан Роулинг',
            'driver': False,
            'phd': False,
            'description': 'Первая книга о магическом мире Гарри Поттера'
        },
        {
            'title': 'Властелин Колец',
            'author': 'Дж. Р. Р. Толкин',
            'driver': False,
            'phd': False,
            'description': 'Эпическая фэнтези-сага о борьбе за Кольцо Всевластия'
        },
        {
            'title': 'Мастер и Маргарита',
            'author': 'Михаил Булгаков',
            'driver': False,
            'phd': False,
            'description': 'Аллегорический роман о дьяволе, который посещает СССР'
        },
        {
            'title': 'Война и мир',
            'author': 'Лев Толстой',
            'driver': False,
            'phd': False,
            'description': 'Эпопея о войне 1812 года и русском обществе'
        },
        {
            'title': 'Преступление и наказание',
            'author': 'Федор Достоевский',
            'driver': False,
            'phd': False,
            'description': 'Роман о моральных кризисах и наказании'
        },
        {
            'title': 'Алиса в Стране чудес',
            'author': 'Льюис Кэрролл',
            'driver': False,
            'phd': False,
            'description': 'Фантастический роман о приключениях девочки в стране чудес'
        },
        {
            'title': 'Три товарища',
            'author': 'Эрих Мария Ремарк',
            'driver': False,
            'phd': False,
            'description': 'Роман о дружбе, любви и потерях в годы Великой депрессии'
        },
        {
            'title': 'Мёртвые души',
            'author': 'Николай Гоголь',
            'driver': False,
            'phd': False,
            'description': 'Сатирический роман о мелкомещанской России'
        },
        {
            'title': '[ДАННЫЕ УДАЛЕНЫ]',
            'author': 'УРАЛЬСКИЙ НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ ИНСТИТУТ УЦУЦУГИ',
            'driver': True,
            'phd': True,
            'description': 'Книга для детей и взрослых',
            'givesFlag': True
        }
]
