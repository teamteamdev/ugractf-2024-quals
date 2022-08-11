FROM imachug/kyzylborda_lib
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["gunicorn", "-b", "unix:/tmp/app.sock", "server:make_app()"]