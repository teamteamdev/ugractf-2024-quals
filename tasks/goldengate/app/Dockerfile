FROM alpine
RUN adduser -D ugra
RUN rm /*bin/*grep
COPY --chmod=755 auth.sh /auth.sh
ENV ENV=/auth.sh
CMD ["sh"]
