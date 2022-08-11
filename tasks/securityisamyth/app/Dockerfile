FROM imachug/kyzylborda_lib
RUN apk add --no-cache gcc musl-dev gmp-dev mpfr-dev mpc1-dev
# Stable gmpy is incompatible with CPython 3.12
RUN pip3 install gmpy2==2.2.0a1
WORKDIR /app
CMD ["python3", "-m", "kyzylborda_lib.server", "unix:/tmp/app.sock", "server"]
