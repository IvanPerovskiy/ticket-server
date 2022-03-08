##
# image
#
FROM nginx:alpine

ARG UID
ARG GID

# bash
RUN apk add --no-cache bash

# wait-for-it
RUN wget https://github.com/vishnubob/wait-for-it/raw/master/wait-for-it.sh -O /usr/local/bin/wait-for-it && \
    sed -i 's/WAITFORIT_BUSYTIMEFLAG="-t"/WAITFORIT_BUSYTIMEFLAG=""/g' /usr/local/bin/wait-for-it && \
    chmod a+x /usr/local/bin/wait-for-it

# openssl
RUN apk add --no-cache openssl

# user
RUN adduser -u ${UID} -D app
USER app
RUN mkdir /home/app/temp && \
    mkdir /home/app/log

# certs
RUN openssl req -x509 -nodes -newkey rsa:2048 -keyout /home/app/myboostr.key -out /home/app/myboostr.crt -subj /CN=local.myboostr.ru && \
    chmod 600 /home/app/myboostr.key

# nginx
COPY --chown=app:app nginx.conf /home/app/nginx.conf

WORKDIR /home/app
