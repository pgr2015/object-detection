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

ARG IMAGE_TAG=latest

# build the things required to create the docker image
FROM bonseyes-base:${IMAGE_TAG} as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            git curl npm \
            wget unzip gcc uuid-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/nodejs /usr/bin/node

RUN npm install -g bower

WORKDIR /app

ADD base/containers/dashboard /app

RUN cd static && bower install --force-latest --allow-root

# create the actual docker image
FROM bonseyes-base:${IMAGE_TAG}

RUN apt-get update && \
    apt-get install -y --no-install-recommends libc-ares2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD base/containers/dashboard /app

COPY --from=builder /app/static/bower_components /app/static/bower_components

RUN mkdir /containers && chown www-data /containers