import datetime
import re
import os.path
from email import generator
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from kyzylborda_lib.generator import get_attachments_dir
from kyzylborda_lib.secrets import get_flag

CLEANR = re.compile('<.*?>') 

SENDER = "a.malinov.1964@yandex.ru"
RECEIVER = "vova.petroff@example.org"
RECEIVED = datetime.datetime(2024, 1, 9, 13, 37, 1)

LETTERS = {
    x: chr(ord(x) + 0xfee0)
    for x in "abcdefghijklmnopqrstuvwxyz0123456789_"
}

HEADERS = [
    ("Received", f"from localhost (HELO queue) (127.0.0.1) by localhost with SMTP; {RECEIVED.strftime('%d %b %Y %H:%M:%S')} +0200"),
    ("Received", f"from output21.mail.ovh.net (164.132.34.21) by mail.ovh.net with AES256-GCM-SHA384 encrypted SMTP; {RECEIVED.strftime('%d %b %Y %H:%M:%S')} +0200"),
    ("Received", f"from mail-nwsmtp-mxback-production-main-69.sas.yp-c.yandex.net (mail-nwsmtp-mxback-production-main-69.sas.yp-c.yandex.net [IPv6:2a02:6b8:c23:21b5:0:640:f63:0]) by postback22c.mail.yandex.net (Yandex) with ESMTPS id 602065E537 for <{RECEIVER}>; Fri,  9 Feb 2024 20:30:30 +0300 (MSK)"),
    ("Authentication-Results", f"output21.mail.ovh.net; dkim=pass header.i=@{SENDER.split('@')[1]}"),
    ("X-Spam-Status", "No"),
    ("From", SENDER),
    ("To", RECEIVER),
    ("Subject", "Pro nashu konferenciu"),
    ("Message-Id", "51496709450245710952109561@mail.gmail.com"),
    ("X-Mailer", "Thunderbird"),
    ("Return-Path", SENDER),
]

BODY = """
<p style="BACKGROUND: #f2f2f2; TEXT-ALIGN: center; MARGIN: 0in 0in 0pt; LINE-HEIGHT: normal; mso-background-themecolor: background1; mso-background-themeshade: 242">Здравствуйте!</p>

<p style="color: green; font-weight: bold; font-family: Times New Roman, serif; font-size: 14px;">Приглашаем вас на научно-практическую конференцию «Аспекты устройства гражданского кодекса Атлантиды».</p>

<p style="font-family: Times New Roman, serif; font-size: 14px;">С 1 января 2024 года в силу вступает Гражданский кодекс Атлантиды. Это первое издание документа более чем за 2 000 лет. Каждая статья кодекса, как подтверждено официальными данными, обладает уникальной энергетической матрицей, влияющей на общественные процессы.</p>

<p style="color: green; font-weight: bold; font-family: Times New Roman, serif; font-size: 14px;">Команда экспертов, работавшая над кодексом, включала не только юристов, но и специалистов в области энергетики и философии. Кодекс создавался с применением передовых технологий, таких как квантовые вычисления и биоэнергетические исследования. Некоторые статьи, по официальным данным, способны влиять на коллективное сознание и формировать социокультурные тенденции.</p>

<p style="color: green; font-weight: bold; font-family: Times New Roman, serif; font-size: 14px;">Ведущие юристы компании <b style="font-weight: bold; font-size: 18px;">&laquo;ЦЭП Эксперт Плюс&raquo;</b> подготовили обзор правок:</p>

<div style="margin-left: 12pt;">
  <p style="font-family: Times New Roman, serif; font-size: 14px;" title="Текст">

- Общие принципы и основные понятия в техническом регулировании;</p>

<p style="font-family: Times New Roman, serif; font-size: 14px;">- Формы документов, подтверждающие соответствие продукции и правила их заполнения;</p>

<p style="font-family: Times New Roman, serif; font-size: 14px;" title="Текст">- Аспекты получения гражданства Атлантиды;</p>

   <p style="font-family: Times New Roman, serif; font-size: 14px;" title="Текст">- - Рекомендации по идентификации подлинности документов, подтверждающих соответствие продукции (поступающего сырья) обязательным требованиям;</p>

   <p style="font-family: Times New Roman, serif; font-size: 14px;" title="Текст"><strong>- Правовые основы и практика работы</strong></p>

   <p style="font-family: Times New Roman, serif; font-size: 14px;" title="Текст">- Тренининги;</p>
</div>

<p style="color: red; font-family: Times New Roman, serif; font-size: 14px;"><b>Стоимость участия:</b> 10 100 шиллингов. В стоимость включено трех местное размещение в двух местном номере.</p>
<p style="color: red; font-family: Times New Roman, serif; font-size: 14px;"><b>Место проведения:</b> город САНКТ-ПЕТЕРБУРГ, офис компании &laquo;ЦЭП Эксперт Плюс </p>
<div style="background-color: #f2f2f2; text-align: center; padding: 0.1in 0in 1pt; line-height: normal;">
<p style="font-family: Times New Roman, serif; font-size: 14px;">ПРОМОКОД ДЛЯ участия на 101 рубль (со скидкой 9 999 рублей) {promo}</p>
</div>
<p style="font-family: Times New Roman, serif; font-size: 14px;"><b>Спикеры:</b></p>
<p style="font-family: Times New Roman, serif; font-size: 14px;"> - Лазеров Григорий, доктор юридических наук, профессор, заведующий кафедрой теории государства и права Российского университета дружбы народов;</p>
<p style="font-family: Times New Roman, serif; font-size: 14px;"> - Звездочет Владимир, кандидат юридических наук, доцент кафедры теории и истории государства и права Российского университета дружбы народов;</p>
<p style="font-family: Times New Roman, serif; font-size: 14px;"> - Сердцевидов Григорий, студент юридического факультета Российского университета дружбы народов.</p>
</div>
<div><h1 style="font-family: Times New Roman, serif; font-size: 14px;">Фото галерея</h1></div>
<div>
<img src="cid:pic1.jpeg" width="200" height="200" />
<img src="cid:pic2.jpeg" width="200" height="200" />
<img src="cid:pic3.jpeg" width="200" height="200" />
</div>
<div>
<p style="font-family: Times New Roman, serif; font-size: 14px;"><strong>Контакты</strong><br/>
Телефон: +7 (903) 728-89-80, доб. 129</br>
Email: noreply@a.ru</p>
<p style="font-family: Times New Roman, serif; font-size: 24px;">Вы можете отписаться от РАССЫЛОК, отправив нам письмо по голубиной почте.</p>
""".strip()


def create_message(flag: str) -> MIMEMultipart:
    msg = MIMEMultipart('related')
    ct = msg["Content-Type"]
    del msg["Content-Type"]
    for header, value in HEADERS:
        msg.add_header(header, value)
    msg.add_header("Content-Type", ct)
    msg.preamble = "This is a multi-part message in MIME format."

    alternative = MIMEMultipart("alternative")
    msg.attach(alternative)

    text = BODY.format(promo=flag).encode().decode('cp1251')

    alternative.attach(MIMEText(text, "html", "utf-8"))
    alternative.attach(MIMEText(CLEANR.sub("", text), "plain", "utf-8"))
    for img in ["pic1", "pic2", "pic3"]:
        imgpart = MIMEImage(open(f"private/{img}.jpeg", "rb").read())
        imgpart.add_header("Content-ID", f"<{img}.jpeg>")
        msg.attach(imgpart)

    return msg

def write_eml_file(msg: MIMEMultipart, target: str):
    with open(os.path.join(target, "inbox.eml"), "w") as output:
        eml_generator = generator.Generator(output)
        eml_generator.flatten(msg)


def generate():
    flag = "".join([
        LETTERS[x]
        for x in get_flag()
    ])
    msg = create_message(flag)
    write_eml_file(msg, get_attachments_dir())
