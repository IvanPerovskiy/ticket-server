FROM python:3.8

ARG UID
ARG GID

# non interactive
ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN true

# virtualenv
RUN pip install virtualenv

# clear tmp
RUN rm -rf /tmp/*

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
