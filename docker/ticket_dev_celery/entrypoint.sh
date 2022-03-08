#!/bin/sh
set -e
set -x

READY=/home/app/env/ready

if [ ! -f ${READY} ]; then
    cd /home/app
    virtualenv env
    . env/bin/activate
    pip install --upgrade pip

    touch ${READY}
    deactivate
    cd /home/app/src
fi

. /home/app/env/bin/activate
pip install -r requirements.txt


exec "$@"
