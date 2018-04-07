# Submitting pythonic application via spark-submit in mesos cluster containarized by docker

1. [Overview](#Overview)
   * [Docker Image](#DockerImage)
   * [Deployment](#Deployment)
   * [Issue](#Issue)

## Overview

   The idea of such modus operandi is to promote the application of BIG DATA in a resources-optimized and streamline-egonomics envisioned by CMS BIG DATA project. The docker offers standardized container to facilitate deployment of spark framework, addressing streamline-egonomics; and using Mesos to monitor and optimize resources allocation Spark's operation, consititutes the resources-optimized element.

### Docker Image

    The docker image is built based on CentOs with XrootD-Hadoop-Connector compiled on the fly. By default the docker image is capable to accessing EOS storage. Currently docker images [siewyanhoh/shohmesos:v3](https://hub.docker.com/r/siewyanhoh/shohmesos/) is working. DockerFile used is [here](https://github.com/SiewYan/BIGDATA-1/blob/docker_dev/Docker_dev/DockerFiles/Dockerfile_v3).

### Deployment

    The example code is used to prove the working concept is ```Zpeak_nano_multipledataset.py```, deploying the docker container together with spark application done via [script](https://github.com/SiewYan/BIGDATA-1/blob/docker_dev/Docker_dev/deploy_docker.sh). Monitoring webpage for Mesos is ```10.64.22.90:5050```.

### Issue

    - [ ] Insufficient resources in executor/slave issue
    - [ ] Task is not visible in UI webpage while the application is running. (Zpeak_nano_multipledataset.py)
    - [ ] SecurityManager reports authentication disable, is this expected launching on top of Mesos cluster?
    - [ ] The deploy mode cluster return error on empty server response. Need MesosDispatcher ? 