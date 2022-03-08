FROM python:3.8

ARG UID
ARG GID

# non interactive
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

RUN apt-get update && \
    apt-get install -y vim && \
    apt-get install -y graphviz && \
    apt-get install -y wkhtmltopdf

# wait-for-it
RUN wget https://github.com/vishnubob/wait-for-it/raw/master/wait-for-it.sh -O /usr/local/bin/wait-for-it && \
    chmod a+x /usr/local/bin/wait-for-it

# virtualenv
RUN pip install virtualenv

# user
RUN adduser -u ${UID} --disabled-password --gecos "" app
RUN mkdir /src && \
    chown ${UID}:${GID} /src
USER app
RUN mkdir /home/app/env

# entrypoint.sh
COPY --chown=app:app entrypoint.sh /home/app/entrypoint.sh
RUN chmod u+x /home/app/entrypoint.sh

# bstr
RUN ln -s /src /home/app
ENV DJANGO_SETTINGS_MODULE=ticket_server.dev_settings

WORKDIR /home/app/src
