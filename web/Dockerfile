FROM ubuntu:18.04

RUN apt update -y && apt install python3 -y \
    && apt install python3-pip -y \
    && apt install libpq-dev -y \
    && apt install graphviz -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/

RUN pip3 install -r requirements.txt