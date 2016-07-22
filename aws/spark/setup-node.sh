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
#

cd /cosr/back && sudo /usr/local/bin/pip install -r requirements.txt --upgrade
