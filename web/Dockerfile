#FROM ubuntu:18.04
#FROM debian:10
FROM python:3.9-slim

RUN apt update -y && apt install python3.9 -y \
    && apt install python3-pip -y \
    && apt install libpq-dev -y \
    && apt install graphviz -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/

RUN pip3 install -r requirements.txt
COPY . /code/
