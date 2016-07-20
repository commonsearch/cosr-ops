# Notes on our Spark images for AWS

We are using Packer to build our custom Spark AMIs.

They are based on the latest [Amazon Linux AMI](https://aws.amazon.com/amazon-linux-ami/), on top of which we add our requirements, much like we do in the `cosr-back` [Dockerfile](https://github.com/commonsearch/cosr-back/blob/master/Dockerfile)