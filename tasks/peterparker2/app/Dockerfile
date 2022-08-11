FROM imachug/kyzylborda_lib
RUN apk add --no-cache texlive texlive-dvi texmf-dist-latexextra
RUN pip install gunicorn
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["gunicorn", "-b", "unix:/tmp/app.sock", "server:app"]
