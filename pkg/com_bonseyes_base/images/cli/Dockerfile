FROM ubuntu:xenial

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            python3 python3-pip python3-setuptools python3-wheel && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD images/cli/requirements.txt /
RUN pip3 install -r /requirements.txt

RUN pip3 install --upgrade pip==9.0.3 && pip3 install cbor==1.0.0 pydevd numpy h5py

ENV PATH ${PATH}:/app/com_bonseyes_base/bin

ADD bin /app/com_bonseyes_base/bin
ADD lib /app/com_bonseyes_base/lib
ADD formats /app/com_bonseyes_base/formats

WORKDIR /data

ENTRYPOINT [ "/app/com_bonseyes_base/bin/be-admin" ]
