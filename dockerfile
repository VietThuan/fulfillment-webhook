FROM sgoblin/python3.5:latest
MAINTAINER [n]

ENV LANG=C.UTF-8

RUN apt-get update

# install pip3
RUN apt-get -y install python3-pip
RUN pip3 install --upgrade pip


COPY ./requirements.txt /
RUN pip3 install -r /requirements.txt


# install nano
RUN ["apt-get", "install", "-y", "nano"]

ENTRYPOINT  cd /code/ && python3 app.py