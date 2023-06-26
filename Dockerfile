# syntax=docker/dockerfile:1
FROM python:3.11-alpine
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV CONFIG_FILE=/code/config.yml
RUN apk add --no-cache bash gcc musl-dev linux-headers libffi-dev
COPY code/requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY code .
CMD ["flask", "run"]
