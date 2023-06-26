#!/bin/bash

# for building rpm and deb packages via fpm
CURRENT_DIR=$(pwd)
export LANG=en_US.UTF-8
export VIRTUAL_ENV=${CURRENT_DIR}/build/opt/venv/anyadmin
export PATH=${VIRTUAL_ENV}/bin:${PATH}

install -d \
    build/ \
    build/etc/anyadmin \

python3 -m venv build/opt/venv/anyadmin/
pip install --upgrade pip
pip install --requirement ./code/requirements.txt

# config file
rsync -avP example/config.yml build/etc/anyadmin/

# project files
rsync -avP \
    --delete-excluded \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.py[cod]' \
    --exclude='*$py.class' \
    ./code/ build/opt/venv/anyadmin/web/

# fixed venv paths
perl -i -pe"s|${CURRENT_DIR}/build/|/|" $(grep -rl "${CURRENT_DIR}/" build/ | grep -v '\.pyc') || exit 1
