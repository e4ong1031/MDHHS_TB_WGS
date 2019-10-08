FROM ubuntu:16.04

###################################
# MDHHS MTB WGS Assembly Pipeline #
###################################

MAINTAINER Edison Ong <edong@umich.edu>

RUN mkdir -p /tmp/results && chmod 777 /tmp/results

WORKDIR /app

COPY . /app

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y default-jre

RUN apt-get install -y python
RUN apt-get install -y python3.6 python3-pip
RUN python3.6 -m pip install multiqc==1.7

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8


ENTRYPOINT ["/usr/bin/env"]
CMD ["python3.6", "Assemble.py"]
