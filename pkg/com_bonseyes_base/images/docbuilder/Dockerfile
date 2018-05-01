FROM ubuntu:xenial

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            python3 python3-pip python3-setuptools python3-wheel make graphviz && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install Sphinx

WORKDIR /data