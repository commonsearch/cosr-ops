
#
# Available configuration variables and their defaults
#

COSR_AWS_STACKNAME      := $(shell python aws/config.py AWS_STACKNAME)
COSR_AWS_REGION         := $(shell python aws/config.py AWS_REGION)


# Path to your local install of Spark
SPARK_DIR			?= ../spark-1.6.0



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
