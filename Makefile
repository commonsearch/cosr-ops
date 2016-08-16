PWD := $(shell pwd)

#
# Available configuration variables and their defaults
#

COSR_AWS_STACKNAME      := $(shell python aws/config.py AWS_STACKNAME)
COSR_AWS_REGION         := $(shell python aws/config.py AWS_REGION)


# Path to your local install of Spark
SPARK_CLUSTER_NAME	?= cosr
SPARK_COSR_BACK_TAG  ?= ""


#
# General commands
#

# Runs all available tests on this repository
test:
	make aws_elasticsearch_validate


#
# Commands for the local Docker image
#

# Build the image locally
docker_build:
	make docker_hash > .dockerhash
	docker build -t commonsearch/local-ops .

# Login into the container
docker_shell: docker_check
	docker run -v "$(PWD):/cosr/ops:rw" -v "$(PWD)/../cosr-back/:/cosr/back:rw" -w /cosr/ops -i -t commonsearch/local-ops bash

# Logins into the same container again
docker_reshell:
	sh -c 'docker exec -t -i `docker ps | grep commonsearch/local-ops | cut -f 1 -d " "` bash'

# Pulls the image from Docker hub
docker_pull:
	docker pull commonsearch/local-ops

# Checks if the container is out of date
docker_check:
	@bash -c 'docker run -v "$(PWD):/cosr/ops:ro" -t commonsearch/local-ops sh -c "if diff -q /cosr/.ops-dockerhash /cosr/ops/.dockerhash > /dev/null; then echo \"Docker image is up to date\"; else echo \"\nWARNING: Your Docker image seems to be out of date! Please exit and do \\\"make docker_build\\\" again to avoid any issues.\n\"; fi"'

# Build a unique hash to indicate that a docker_build may be necessary again
docker_hash:
	@sh -c 'cat requirements.txt Dockerfile requirements3.txt | grep -vE "^\s*\#" | grep -vE "^\s*$$" | openssl md5'


#
# AWS Elasticsearch commands
#

# View the CloudFormation template
aws_elasticsearch_template:
	python aws/cloudformation/template-elasticsearch.py --pretty

# Build the CloudFormation template
aws_elasticsearch_build:
	python aws/cloudformation/template-elasticsearch.py > /tmp/cloudformation-elasticsearch-template.json

# Validate the CloudFormation template
aws_elasticsearch_validate: aws_elasticsearch_build
	template=$$(cat /tmp/cloudformation-elasticsearch-template.json) ;\
	aws cloudformation validate-template --template-body "$$template"

# Create the CloudFormation stack on AWS
aws_elasticsearch_create: aws_elasticsearch_validate
	aws cloudformation create-stack \
		--stack-name $(COSR_AWS_STACKNAME)-elasticsearch \
		--region $(COSR_AWS_REGION) \
		--capabilities CAPABILITY_IAM \
		--template-body file:///tmp/cloudformation-elasticsearch-template.json \
		--parameters ParameterKey=ElasticsearchClusterName,ParameterValue=cosr-es-cluster-$(COSR_AWS_STACKNAME)

# Update the CloudFormation stack on AWS in-place
aws_elasticsearch_update: aws_elasticsearch_validate
	aws cloudformation update-stack \
		--stack-name $(COSR_AWS_STACKNAME)-elasticsearch \
		--region $(COSR_AWS_REGION) \
		--capabilities CAPABILITY_IAM \
		--template-body file:///tmp/cloudformation-elasticsearch-template.json \
		--parameters ParameterKey=ElasticsearchClusterName,ParameterValue=cosr-es-cluster-$(COSR_AWS_STACKNAME)

# Delete the CloudFormation stack
aws_elasticsearch_delete:
	aws cloudformation delete-stack --stack-name $(COSR_AWS_STACKNAME)-elasticsearch

# Get metadata about the CloudFormation stack
aws_elasticsearch_describe:
	aws cloudformation describe-stacks --stack-name $(COSR_AWS_STACKNAME)-elasticsearch --region $(COSR_AWS_REGION)

# List events from the CloudFormation stack
aws_elasticsearch_events:
	aws cloudformation describe-stack-events --stack-name $(COSR_AWS_STACKNAME)-elasticsearch --region $(COSR_AWS_REGION)

# Watch events from the CloudFormation stack
aws_elasticsearch_watch:
	watch --interval 5 "bash -c 'make aws_elasticsearch_events | head -100'"


#
# AWS Spark commands
#

# Build a new Spark Amazon Machine Image
aws_spark_build_ami:
	packer build aws/spark/ami/packer-ami-template.json

# Create a Spark cluster using Flintrock
aws_spark_flintrock_create:
	flintrock launch $(SPARK_CLUSTER_NAME) --spark-download-source https://s3.amazonaws.com/packages.commonsearch.org/spark/spark-2.0.1-SNAPSHOT-bin-hadoop2.7.tgz
	make aws_spark_flintrock_setup
	flintrock login $(SPARK_CLUSTER_NAME)

# Update the Spark cluster with the config
aws_spark_flintrock_setup:
	flintrock copy-file $(SPARK_CLUSTER_NAME) aws/spark/setup-node.sh /cosr/
	flintrock run-command $(SPARK_CLUSTER_NAME) 'COSR_BACK_TAG=$(SPARK_COSR_BACK_TAG) bash /cosr/setup-node.sh'
	flintrock copy-file $(SPARK_CLUSTER_NAME) configs/cosr-back.prod.json /cosr/back/cosr-config.json
	flintrock describe $(SPARK_CLUSTER_NAME)

# Restart the Spark cluster and empty its caches
aws_spark_flintrock_restart:
	flintrock run-command $(SPARK_CLUSTER_NAME) --master-only "/home/ec2-user/spark/sbin/stop-slaves.sh && /home/ec2-user/spark/sbin/stop-master.sh"
	flintrock run-command $(SPARK_CLUSTER_NAME) "rm -rf /media/root/spark && rm -rf /home/ec2-user/spark/work"
	flintrock run-command $(SPARK_CLUSTER_NAME) --master-only "/home/ec2-user/spark/sbin/start-master.sh && /home/ec2-user/spark/sbin/start-slaves.sh"
