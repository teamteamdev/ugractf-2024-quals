FROM alpine
RUN adduser -D alarm && crontab -u alarm -
COPY ring-alarm /bin/ring-alarm
USER alarm
RUN touch /home/alarm/logs
USER root
CMD ["crond", "-f", "-L", "/var/log/crond"]
