# syntax=docker/dockerfile:1
FROM python:3.11-alpine

ARG REPO_DIR=.

WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV CONFIG_FILE=/etc/any-sync-admin/config.yml
RUN apk add --no-cache bash gcc musl-dev linux-headers libffi-dev
COPY ${REPO_DIR}/code/ .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD python app.py
