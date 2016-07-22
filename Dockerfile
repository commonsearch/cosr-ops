FROM debian:jessie

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    gcc \
    ssh \
    build-essential \
    make \
    python \
    python-pip \
    python-dev \
    python3 \
    python3-pip \
    python3-dev \
    vim \
    net-tools \
    unzip \
    libyaml-dev


#
# Install Packer
# (conveniently ships as a single executable)
#

RUN wget 'https://releases.hashicorp.com/packer/0.10.1/packer_0.10.1_linux_amd64.zip' && \
	unzip packer_0.10.1_linux_amd64.zip -d /usr/local/bin/ && \
	rm -rf packer_0.10.1_linux_amd64.zip


#
# Python setup
#

ADD requirements.txt /requirements.txt

# Upgrade pip because debian has a really old version
RUN pip install --upgrade --ignore-installed pip

RUN pip install -r /requirements.txt


#
# Python3 setup
#

ADD requirements3.txt /requirements3.txt

# Upgrade pip because debian has a really old version
RUN pip3 install --upgrade --ignore-installed pip

RUN pip3 install -r /requirements3.txt


ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8