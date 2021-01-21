FROM python:3.7

MAINTAINER Askhat Baimukhamedov <askhat.orsk@gmail.com>

RUN apt-get update &&\
    mkdir /opt/project/

COPY requirements.txt /opt/project/requirements.txt

WORKDIR /opt/project/
RUN pip install -r requirements.txt
COPY . /opt/project/

VOLUME /datasets
CMD ["python", "/opt/project/src/main.py"]
