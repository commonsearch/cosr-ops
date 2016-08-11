#!/bin/bash

set -e

#
# Download cosr-back on the node
#

sudo rm -rf /cosr/back && mkdir -p /cosr/back
git clone https://github.com/commonsearch/cosr-back.git /cosr/back


if [-n "$COSR_BACK_TAG"]; then
    cd /cosr/back && git checkout $COSR_BACK_TAG
fi

#
# Setup dependencies
# They are already installed in the AMI but some versions might have been bumped on GitHub since then.
#

cd /cosr/back && sudo /usr/local/bin/pip install -r requirements.txt --upgrade

sudo mkdir -p /usr/spark/packages/jars && sudo chown -R ec2-user /usr/spark/packages
