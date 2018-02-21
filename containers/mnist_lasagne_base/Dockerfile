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
FROM bonseyes-base-gpu:${IMAGE_TAG}


RUN apt-get update && apt-get install -y --no-install-recommends \
	python3-numpy \
	python3-scipy \
	python3-pip \
	python3-requests \
	python3-wheel \
	python3-setuptools \
	python3-matplotlib \
	python3-dev \
	libglib2.0 \
	cmake \
	unzip \
	wget \
	&& \
    rm -rf /var/lib/apt/lists/*

# libglib2.0 is for python-opencv

# install cython required by libgpuarray
RUN pip3 install Cython

# Set CUDA_ROOT used by theano to find CUDA
ENV CUDA_ROOT /usr/local/cuda

# Clone libgpuarray repo and move into it
RUN cd /root && \
  wget https://github.com/Theano/libgpuarray/archive/4ac185c4af9524320628e299a9c6e448fc73b23a.zip && \
  unzip *.zip && \
  cd libgpuarray-* && \
# Make and move into build directory
  mkdir Build && cd Build && \
# CMake
  cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr && \
# Make
  make -j"$(nproc)" && \
  make install && \
# Install pygpu
  cd /root/libgpuarray-* && \
  python3 setup.py build_ext -L /usr/lib -I /usr/include && \
  python3 setup.py install && \
# Delete the build stuff
  rm -rf /root/libgpuarray-*

RUN mkdir /var/www && chown www-data.www-data /var/www

# Set up .theanorc for CUDA
RUN echo "[global]\ndevice=cuda\nfloatX=float32\noptimizer_including=cudnn\n[lib]\ncnmem=0.1\n[nvcc]\nfastmath=True" > /var/www/.theanorc

# install all the python packages that are not in ubuntu yet
RUN pip3 install Theano==0.9.0 \
         https://github.com/Lasagne/Lasagne/archive/b1e5bc468a2fbc5e5d026f6d1c6170b80e8be224.zip

RUN pip3 install h5py

# theano wants to write stuff in the home
ENV HOME /var/www