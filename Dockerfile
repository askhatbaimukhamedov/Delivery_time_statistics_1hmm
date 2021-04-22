FROM python:3.7

MAINTAINER Askhat Baimukhamedov <askhat.orsk@gmail.com>

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean

RUN mkdir /opt/project
COPY . /opt/project
WORKDIR /opt/project

COPY requirements.txt /opt/project/requirements.txt

VOLUME /logs

RUN pip install --upgrade pip \
    pip install -r requirements.txt

CMD ["python", "/opt/project/src/main.py"]
