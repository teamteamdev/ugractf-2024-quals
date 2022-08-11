FROM imachug/kyzylborda_lib
RUN apk add --no-cache gcc musl-dev linux-headers
RUN pip install gunicorn
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
CMD ["gunicorn", "-b", "unix:/tmp/app.sock", "server:make_app(\"/state\")", "--worker-class", "aiohttp.GunicornWebWorker"]
