FROM amazoncorretto:19-alpine-jdk
RUN apk add --no-cache unzip curl \
  && mkdir -p /app/gradle \
  && cd /app/gradle \
  && curl -L -o gradle-bin.zip https://services.gradle.org/distributions/gradle-8.6-bin.zip \
  && unzip "gradle-bin.zip" \
  && rm "gradle-bin.zip" \ 
  && apk del unzip curl
COPY . /app/project
WORKDIR /app/project
RUN /app/gradle/gradle-8.6/bin/gradle jar

FROM amazoncorretto:19-alpine
COPY --from=0 /app/project/build/libs/uzh-server.jar /app/uzh-server.jar
EXPOSE 9276
CMD ["java", "-jar", "/app/uzh-server.jar"]

