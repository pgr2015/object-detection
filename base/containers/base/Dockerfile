#
# NVISO CONFIDENTIAL
#
# Copyright (c) 2017 nViso SA. All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") is the confidential and proprietary information
# owned by nViso or its suppliers or licensors.  Title to the  Material remains
# with nViso SA or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of nViso or its
# suppliers and licensors. The Material is protected by worldwide copyright and trade
# secret laws and treaty provisions. You shall not disclose such Confidential
# Information and shall use it only in accordance with the terms of the license
# agreement you entered into with nViso.
#
# NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
# THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
# DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
#
ARG base_image=ubuntu:xenial
FROM ${base_image}

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            python3 python3-pip python3-setuptools python3-wheel \
            uwsgi-plugin-python3 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip && pip3 install Flask requests uwsgidecorators pyyaml

ADD base/containers/base/configs/uwsgi.ini /etc/uwsgi/

WORKDIR /app

ADD base/containers/base/app /app
ADD base/code /app
ADD base/common /app

ENV PYTHONPATH /app

EXPOSE 80

RUN mkdir /data && chown -R www-data.www-data /data

CMD ["/usr/bin/uwsgi", "--ini", "/etc/uwsgi/uwsgi.ini", "--ini", "/app/app.ini"]
