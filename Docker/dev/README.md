# Submitting pythonic application via spark-submit in mesos cluster containarized by docker

1. [Overview](#Overview)
   * [Docker Image](#DockerImage)
   * [Deployment](#Deployment)
   * [Issue](#Issue)
   * [To-do](#To-do)

## Overview

   The idea of such modus operandi is to promote the application of BIG DATA in a resources-optimized and streamline-egonomics envisioned by CMS BIG DATA project. The docker offers standardized container to facilitate deployment of spark framework, addressing streamline-egonomics; and using Mesos to monitor and optimize resources allocation Spark's operation, consititutes the resources-optimized element.

### Docker Image

   The docker image is built based on CentOs with XrootD-Hadoop-Connector compiled on the fly. By default the docker image is capable to accessing EOS storage. Currently docker images [siewyanhoh/shohmesos:v3](https://hub.docker.com/r/siewyanhoh/shohmesos/) is working. DockerFile used is [here](https://github.com/SiewYan/BIGDATA-1/blob/docker_dev/Docker_dev/DockerFiles/Dockerfile_v3).

#### Update

   ~~Recommended images are [siewyanhoh/shohmesos:Spark221](https://github.com/SiewYan/BIGDATA-1/blob/docker_dev/Docker_dev/DockerFiles/Dockerfile_221) and [siewyanhoh/shohmesos:Spark230](https://github.com/SiewYan/BIGDATA-1/blob/docker_dev/Docker_dev/DockerFiles/Dockerfile_230_grid).~~

## Deployment

   Deploying application in Spark standalone and Mesos (via docker)

#### Deploy in Spark standalone cluster `10.64.22.198:7077`

   Setup ssh double tunneling
   ```
   ssh -t -L 11198:localhost:11198 USER@gate.pd.infn.it ssh -L 11198:localhost:11198 USER@10.64.22.198
   ```

   Clone the package
   ```
   git clone -b docker_dev https://github.com/SiewYan/BIGDATA-1.git
   ```

   Application can be submitted via `spark-submit` and `jupyter notebook`
   
   ```
   cd BIGDATA-1/Docker_dev/scripts
   #check the boolean $submit to switch between two submission
   sh deploy_SPARK.sh
   ```

#### Deploy in Mesos cluster `10.64.22.90:5050`

   Setup ssh double tunneling
   ```
   ssh -t -L 1190:localhost:1190 USER@gate.pd.infn.it ssh -L 1190:localhost:1190 USER@10.64.22.90
   ```

   Clone the package
   ```
   git clone -b	docker_dev https://github.com/SiewYan/BIGDATA-1.git
   ```

   Application can be submitted	via `spark-submit` and `jupyter notebook`

   ```
   cd BIGDATA-1/Docker_dev/scripts
   #check the boolean $submit to switch	between	two submission
   sh deploy_MESOS.sh
   ```

### Issue

1. Issues (tick box means solved):
   - [x] Insufficient resources in executor/slave issue (turn out the master could not listen to slave port)
   - [x] Task is not visible in UI webpage while the application is running. (Zpeak_nano_multipledataset.py)
   - [ ] SecurityManager reports authentication disable, is this expected launching on top of Mesos cluster?
   - [ ] The deploy mode cluster return error on empty server response. Need MesosDispatcher ? 
   - [x] Insufficient resources in executor/slave in notebook mode.

### To-do

1. Deploy client-mode with Mesos on:
   - [x] Data Analysis Application
   - [x] Machine Learning Application
   - [ ] Data Streaming	Application

2. Deploy cluster-mode with Mesos on:
   - [ ] Data Analysis Application
   - [ ] Machine Learning Application
   - [ ] Data Streaming Application

3. Docker deployment on:
   - [x] Data Analysis Application
   - [x] Machine Learning Application
   - [ ] Data Streaming Application

4. Metrics observality (deploy at SWAN or using sparkMeasure) on:
   - [ ] Data Analysis Application
   - [ ] Machine Learning Application
   - [ ] Data Streaming	Application

5. Define and review the demo code on:
   - [ ] Data Analysis Application: Spark-root on data file conflict with spark 2.3.0
   - [ ] Machine Learning Application: Need more input to define the entire study 
   - [ ] Data Streaming Application

6. Jupyterhub (possibly)