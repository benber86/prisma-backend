FROM python:3.10.5-slim-bullseye

ENV CELERY_BROKER_URL=redis://redis:6379/0
ENV CELERY_RESULT_BACKEND=redis://redis:6379/0
ENV C_FORCE_ROOT=true

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

ENV DEBUG=0
ENV DEV=0

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc libc-dev libpq-dev python-dev netcat && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN pip install -U setuptools pip
RUN pip install -r requirements.txt
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
