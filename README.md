# cosr-ops

This repository contains the tools needed for managing the operations of [Common Search](https://about.commonsearch.org/). A demo is currently hosted on [uidemo.commonsearch.org](https://uidemo.commonsearch.org/)

Help is welcome! We have a complete guide on [how to contribute](CONTRIBUTING.md).


## Understand the project

We have an [early documentation](https://about.commonsearch.org/developer/operations) available for operations.

In a nutshell, 2 components are managed from this repository:

- Our Elasticsearch cluster, using [AWS CloudFormation](https://aws.amazon.com/cloudformation/).
- Our [Backend](/developer/backend), using the [Spark EC2 scripts](http://spark.apache.org/docs/latest/ec2-scripts.html).

Here is how they fit in our [current infrastructure](https://about.commonsearch.org/developer/architecture):

![General technical architecture of Common Search](https://about.commonsearch.org/images/developer/architecture-2016-02.svg)

## Local install

A complete guide available in [INSTALL.md](INSTALL.md).


## Creating a configuration file

You will need to create a `configs/cosr-ops.prod.json` with the following template:

```
{
	"AWS_STACKNAME": "mystack",

	"AWS_REGION": "us-east-1",
	"AWS_ZONE": "us-east-1a",
	"AWS_SUBNET": "subnet-xxxxxx",
	"AWS_VPC": "vpc-xxxxxxx",
	"AWS_SECURITYGROUP": "sg-xxxxxxx",

	"AWS_KEYNAME": "mykeyname",
	"AWS_USER": "root",

	"AWS_SPARK_AMI": "ami-668dba0c",
	"AWS_SPARK_SPOTBID": "0.1",
	"AWS_SPARK_INSTANCETYPE_MASTER": "c4.xlarge",
	"AWS_SPARK_INSTANCETYPE_WORKER": "c4.xlarge",
	"AWS_SPARK_WORKER_COUNT": 15,
	"AWS_SPARK_VERSION": "1.6.0",
	"AWS_SPARK_PLACEMENTGROUP": "myplacementgroup",

	"SPARK_PATH": "../spark-1.6.0"
}
```