
#
# Available configuration variables and their defaults
#

COSR_AWS_STACKNAME      := $(shell python aws/config.py AWS_STACKNAME)
COSR_AWS_REGION         := $(shell python aws/config.py AWS_REGION)


# Path to your local install of Spark
SPARK_DIR			?= ../spark-1.6.0
SPARK_CLUSTER_NAME	?= test-flintrock2
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
	docker build -t commonsearch/local-ops .

# Login into the container
docker_shell:
	docker run -v "$(PWD):/cosr/ops:rw" -w /cosr/ops -i -t commonsearch/local-ops bash

# Logins into the same container again
docker_reshell:
	sh -c 'docker exec -t -i `docker ps | grep commonsearch/local-ops | cut -f 1 -d " "` bash'

# Pulls the image from Docker hub
docker_pull:
	docker pull commonsearch/local-ops


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

# Create the Spark cluster
aws_spark_create:
	python aws/spark/manage-cluster.py create

# Log in to the Spark master
aws_spark_ssh:
	python aws/spark/manage-cluster.py ssh

# Deploy the cosr-back code on the Spark cluster
aws_spark_deploy_cosrback:
	python aws/spark/deploy-cosr-back.py

# Destroy the Spark cluster
aws_spark_delete:
	python aws/spark/manage-cluster.py delete

# Build a new Spark Amazon Machine Image
aws_spark_build_ami:
	packer build aws/spark/ami/packer-ami-template.json

# New flintrock commands
aws_spark_flintrock_create:
	flintrock --config aws/spark/flintrock/config.yaml launch $(SPARK_CLUSTER_NAME)
	flintrock --config aws/spark/flintrock/config.yaml describe $(SPARK_CLUSTER_NAME)
	flintrock --config aws/spark/flintrock/config.yaml run-command $(SPARK_CLUSTER_NAME) 'sudo chown -R ec2-user /cosr'
	make aws_spark_flintrock_update

aws_spark_flintrock_update:
	flintrock --config aws/spark/flintrock/config.yaml copy-file $(SPARK_CLUSTER_NAME) aws/spark/setup-node.sh /cosr/
	flintrock --config aws/spark/flintrock/config.yaml run-command $(SPARK_CLUSTER_NAME) 'COSR_BACK_TAG=$(SPARK_COSR_BACK_TAG) bash /cosr/setup-node.sh'
	flintrock --config aws/spark/flintrock/config.yaml copy-file $(SPARK_CLUSTER_NAME) configs/cosr-back-esless.prod.json /cosr/back/cosr-config.json
	flintrock --config aws/spark/flintrock/config.yaml login $(SPARK_CLUSTER_NAME)
