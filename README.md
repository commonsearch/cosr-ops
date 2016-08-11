# cosr-ops

This repository contains the tools needed for managing the operations of [Common Search](https://about.commonsearch.org/). A demo is currently hosted on [uidemo.commonsearch.org](https://uidemo.commonsearch.org/)

Help is welcome! We have a complete guide on [how to contribute](CONTRIBUTING.md).


## Understand the project

We have an [early documentation](https://about.commonsearch.org/developer/operations) available for operations.

In a nutshell, 2 components are managed from this repository:

- Our Elasticsearch cluster, using [AWS CloudFormation](https://aws.amazon.com/cloudformation/).
- The Spark cluster for our [Backend](/developer/backend), using [Flintrock](https://github.com/nchammas/flintrock).

Here is how they fit in our [current infrastructure](https://about.commonsearch.org/developer/architecture):

![General technical architecture of Common Search](https://about.commonsearch.org/images/developer/architecture-2016-02.svg)

## Local install

A complete guide available in [INSTALL.md](INSTALL.md).


## Documentation

We have a first tutorial online:

 - [Analyzing the web with Spark on EC2](https://about.commonsearch.org/developer/tutorials/analyzing-the-web-with-spark-on-ec2)


## Provisioning info

### Common Crawl indexing

- On the Spark workers, bottleneck is the CPU so all cores should be at 100% all the time.
- The average CPU time on an EC2 c4 core is 17 minutes per ~1G Common Crawl file.
- The June 2016 crawl has ~20.000 of them, so you need ~5.500 core hours.
- Spot prices can reach as low as $0.01/h per core, so the whole job can be done for less than $60.

### WebGraph generation

- In progress.

### PageRank

- In progress.


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