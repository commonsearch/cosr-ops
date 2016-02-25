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

yum update -y
yum install gcc zlib-devel bzip2-devel snappy-devel libffi-devel autoconf libtool automake openssl-devel strace -y
yum update binutils -y

# Install latest Python
wget https://www.python.org/ftp/python/2.7.11/Python-2.7.11.tgz && \
  tar -zxvf Python-2.7.11.tgz && cd Python-2.7.11 && \
  ./configure && make && make install && \
  cd .. && rm -rf Python-2.7.11 Python-2.7.11.tgz

/usr/local/bin/python -m ensurepip
/usr/local/bin/pip install virtualenv

# RocksDB install
# https://github.com/facebook/rocksdb/blob/master/INSTALL.md
wget https://gflags.googlecode.com/files/gflags-2.0-no-svn-files.tar.gz && \
  tar -xzvf gflags-2.0-no-svn-files.tar.gz && cd gflags-2.0 && \
  ./configure && make && sudo make install && \
  cd .. && rm -rf gflags-2.0-no-svn-files.tar.gz gflags-2.0

wget https://github.com/facebook/rocksdb/archive/v4.1.tar.gz && \
  tar -zxvf v4.1.tar.gz && cd rocksdb-4.1 && \
  make shared_lib && make install && \
  cd .. && rm -rf rocksdb-4.1 v4.1.tar.gz

# Gumbo install
wget https://github.com/google/gumbo-parser/archive/v0.10.1.tar.gz && \
  tar zxf v0.10.1.tar.gz && cd gumbo-parser-0.10.1 && \
  ./autogen.sh && ./configure && make && make install && \
  cd .. && rm -rf gumbo-parser-0.10.1 v0.10.1.tar.gz

ldconfig /usr/local/lib

resize2fs /dev/xvda1

mkdir -p /cosr/back

echo "syntax on" > /root/.vimrc