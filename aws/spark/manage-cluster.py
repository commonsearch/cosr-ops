#!/usr/bin/env python

import os
import sys

sys.path.insert(-1, os.getcwd())

from aws.config import CONFIG
from aws.utils import get_command_from_template

action = sys.argv[1]


if action == "create":
	command = get_command_from_template("""
		{{SPARK_PATH}}/ec2/spark-ec2 launch {{AWS_STACKNAME}}-spark
		-i configs/{{AWS_KEYNAME}}.pem -k {{AWS_KEYNAME}}
		--ami={{AWS_SPARK_AMI}}
		--region={{AWS_REGION}}
		--subnet-id={{AWS_SUBNET}}
		--vpc-id={{AWS_VPC}}
		--spot-price={{AWS_SPARK_SPOTBID}}
		--instance-type={{AWS_SPARK_INSTANCETYPE_WORKER}}
		--spark-version={{AWS_SPARK_VERSION}}
		--master-instance-type={{AWS_SPARK_INSTANCETYPE_MASTER}}
		--zone={{AWS_ZONE}}
		--slaves={{AWS_SPARK_WORKER_COUNT}}
		--placement-group={{AWS_SPARK_PLACEMENTGROUP}}
		--hadoop-major-version=yarn
	""")

	os.system(command)

elif action == "ssh":
	os.system(get_command_from_template("""
		{{SPARK_PATH}}/ec2/spark-ec2 login {{AWS_STACKNAME}}-spark
		-i configs/{{AWS_KEYNAME}}.pem -k {{AWS_KEYNAME}}
	"""))

elif action == "delete":
	os.system(get_command_from_template("""
		{{SPARK_PATH}}/ec2/spark-ec2 destroy {{AWS_STACKNAME}}-spark
	"""))