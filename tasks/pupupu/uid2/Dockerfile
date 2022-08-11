FROM alpine
RUN apk add python3 curl
RUN adduser -D alarm && crontab -u alarm -
COPY ring-alarm /bin/ring-alarm
USER alarm
RUN touch /home/alarm/logs
USER root
RUN echo "0 9 * * 1,2,3,4,5 ring-alarm" | crontab -u alarm -
CMD ["sh", "-c", "ip link add local type dummy && ip addr add 192.168.1.2/24 dev local && ip addr add 192.168.1.3/24 dev local && crond -L /var/log/crond && python3 -m http.server -b 192.168.1.2 -d /root 80"]
