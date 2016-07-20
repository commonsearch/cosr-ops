#!/bin/bash

#
# This is executed by Packer on a temporary AMI to build our custom base AMI
#
# Here we install all the dependencies that might not change very often. Python modules will be
# installed later, on each instance.
#
# This should be somewhat kept in sync with
# https://github.com/commonsearch/cosr-back/blob/master/Dockerfile
#

set -e

sudo yum update -y
sudo yum install git gcc gcc-c++ zlib-devel bzip2-devel snappy-devel libffi-devel autoconf libtool automake openssl-devel strace -y
sudo yum update binutils -y

# Install latest Python
PYTHON_VERSION=2.7.12
wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz && \
  tar -zxf Python-$PYTHON_VERSION.tgz && cd Python-$PYTHON_VERSION && \
  ./configure && make && sudo make install && \
  cd .. && rm -rf Python-$PYTHON_VERSION Python-$PYTHON_VERSION.tgz

sudo /usr/local/bin/python -m ensurepip
sudo /usr/local/bin/pip install virtualenv

# RocksDB install
# https://github.com/facebook/rocksdb/blob/master/INSTALL.md
wget https://gflags.googlecode.com/files/gflags-2.0-no-svn-files.tar.gz && \
  tar -xzf gflags-2.0-no-svn-files.tar.gz && cd gflags-2.0 && \
  ./configure && make && sudo sudo make install && \
  cd .. && rm -rf gflags-2.0-no-svn-files.tar.gz gflags-2.0

wget https://github.com/facebook/rocksdb/archive/v4.1.tar.gz && \
  tar -zxf v4.1.tar.gz && cd rocksdb-4.1 && \
  make shared_lib && sudo make install && \
  cd .. && rm -rf rocksdb-4.1 v4.1.tar.gz

# Gumbo install
wget https://github.com/google/gumbo-parser/archive/v0.10.1.tar.gz && \
  tar zxf v0.10.1.tar.gz && cd gumbo-parser-0.10.1 && \
  ./autogen.sh && ./configure && make && sudo make install && \
  cd .. && rm -rf gumbo-parser-0.10.1 v0.10.1.tar.gz

# RE2 install
RE2_VERSION=636bc71728b7488c43f9441ecfc80bdb1905b3f0
curl -sL https://github.com/google/re2/archive/$RE2_VERSION.tar.gz -o re2.tar.gz && \
  tar zxf re2.tar.gz && cd re2-$RE2_VERSION && \
  make && sudo make install && \
  cd .. && rm -rf re2-$RE2_VERSION re2.tar.gz

# Protocol buffers install
PROTOBUF_VERSION=3.0.0-beta-3.1
wget https://codeload.github.com/google/protobuf/tar.gz/v${PROTOBUF_VERSION} && \
  tar zxf v${PROTOBUF_VERSION} && cd protobuf-${PROTOBUF_VERSION} && \
  ./autogen.sh && ./configure && make && sudo make install && \
  cd .. && rm -rf protobuf-${PROTOBUF_VERSION} v${PROTOBUF_VERSION}


# Pre-install the current Python requirements to speed up further installs
wget https://raw.githubusercontent.com/commonsearch/cosr-back/master/requirements.txt
sudo /usr/local/bin/pip install -r requirements.txt
rm -rf requirements.txt


sudo ldconfig /usr/local/lib



sudo mkdir -p /cosr/back

sudo sh -c 'echo "syntax on" > /root/.vimrc'