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

# user
RUN adduser -u ${UID} -D app
USER app
RUN mkdir /home/app/temp && \
    mkdir /home/app/log

# nginx
COPY --chown=app:app nginx.conf /home/app/nginx.conf

WORKDIR /home/app
