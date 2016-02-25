#!/usr/bin/env python

import os
import sys

sys.path.insert(-1, os.getcwd())

from aws.utils import *
from aws.config import CONFIG


print "Deploying cosr-back on spark cluster '%s-spark'..." % CONFIG["AWS_STACKNAME"]


# Find the master and make there there is only one of them
master_matches = lookup_ec2_instances("%s-spark-master" % CONFIG["AWS_STACKNAME"])
assert len(master_matches) == 1, len(master_matches)
assert len(master_matches[0].instances) == 1
master_instance = master_matches[0].instances[0]

print "Spark master detected: %s" % master_instance.public_dns_name


# Do an ad-hoc patch to the workers. TODO: remove the need for this.
all_spark_instances = lookup_ec2_instances("%s-spark" % CONFIG["AWS_STACKNAME"])
assert all_spark_instances > 1

print "Resizing root volume on %s master & worker instances" % len(all_spark_instances)

# Quite ugly, but there are some mirror failures sometimes. TODO?
for i in range(2):
    for instance in all_spark_instances:
        resize_root_volume(instance.instances[0])

# Send the source + config & import local data on the master
send_cosrback_source(master_instance)
import_cosrback_local_data(master_instance)


# Copy the build dir to all slaves
# TODO: rsync options "--whole-file" lead to more performance
ssh(master_instance,
    '/root/spark-ec2/copy-dir /cosr/back/'
    )
