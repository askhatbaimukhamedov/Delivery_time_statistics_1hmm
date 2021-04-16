FROM python:3.7

MAINTAINER Askhat Baimukhamedov <askhat.orsk@gmail.com>

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean

RUN mkdir /opt/project
COPY . /opt/project
WORKDIR /opt/project

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY requirements.txt /opt/project/requirements.txt

CMD ["python", "/opt/project/src/main.py"]
