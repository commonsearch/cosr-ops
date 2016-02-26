#!/usr/bin/env python

import os
import sys

sys.path.insert(-1, os.getcwd())

from aws.utils import *
from aws.config import CONFIG

name = "%s-explainer" % CONFIG["AWS_STACKNAME"]

instance_matches = lookup_ec2_instances(name)
if len(instance_matches) == 0:

	print "Creating explainer with name '%s'" % name

	instance = create_ec2_instance(name, instance_type="c4.large")

	print "Successfully created: ", instance, instance.public_dns_name

else:
	instance = instance_matches[0].instances[0]
	print "Found existing explainer instance: ", instance

# Send the source + config & import local data on the master
send_cosrback_source(instance)
import_cosrback_local_data(instance)

ssh(instance, "bash")
