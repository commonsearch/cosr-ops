# Installing cosr-ops on your local machine

This guide will take you through everything you need to do to have a fully working install of `cosr-ops` on your local machine.

Please note that we only support Linux and Mac OS X at the moment.



## 1. Install dependencies on your local machine

There are only 2 dependencies you need to install to get started:

- [Docker](http://docker.com) to run containers ([Installation instructions](https://docs.docker.com/engine/installation/))
- [git](http://git-scm.com) to interact with GitHub ([Installation instructions](https://help.github.com/articles/set-up-git/))

You should make sure your Docker daemon is started. Check the [Docker documentation](https://docs.docker.com/engine/installation/) if you are unsure how to start it. For instance on Ubuntu you may need to run `sudo service docker start`.



## 2. Download the code & the Docker images

To clone this repository from GitHub, go to your local workspace directory and run:

```
git clone https://github.com/commonsearch/cosr-ops.git
cd cosr-ops
```

Next, you should download our pre-built image from the Docker Hub:

```
make docker_pull
```

Alternatively, you can do `make docker_build` to build the image again locally.


## 3. You're done!

Congratulations! You should now be able to start diving further in the code of `cosr-ops`.