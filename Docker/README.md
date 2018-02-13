B# Docker

1. [How to create the container](#How-to-create-the-container)
   * [Install Docker in your host](#install-docker-in-your-host)
   * [Creating a Spark image with Dockerfile](#Creating-a-Spark-image-with-Dockerfile)
   ** [Important conf file and script](#Important-conf-file-and-script)
   ** [Build the Docker](#Build-the-Docker)
2. [Use the Spark with Mesos](#Use-the-Spark-with-Mesos)
3. [Documentation](#documentation)

## How to create the container

### install docker in your host

Add the docket repo in your host (superuser):

```
sudo tee /etc/yum.repos.d/docker.repo <<EOF                                                              
[dockerrepo]                                                                                             
name=Docker Repository                                                                                    
baseurl=https://yum.dockerproject.org/repo/main/centos/7/       
enabled=1                                                                                                
gpgcheck=1                                                                                               
gpgkey=https://yum.dockerproject.org/gpg                                                                 
EOF
sudo yum update
```

Install docker and start docker daemon:

```
sudo yum install docker-engine
sudo service docker start
```

If successful, you could be able to inspect the containers that are currently running, which will be none for the moment.

```
#return list of running container
docker ps
#return list of ran container
docker ps -a
```

### Detour

In order to demonstrate the flexibility of docker, consider this little demonstration for the purpose to be awed.


```
#Pull the busybox image from docker registry
sudo docker pull busybox
#Return the list of image in the system
sudo docker images 
#Run echo command inside the container
sudo docker run busybox echo "hello from busybox"
```

In order to run more than just echo on the created container, you may explore the containerised OS by attaching to interactive tty.

```
docker run -it busybox sh
```

Exit by pressing exit.
One good rule of thumb is to clear the container renmants.

```
#Identify used container ID
sudo docker ps -a
#Delete the ran container
sudo docker rm <ID>
```

The detour ends here.

### Creating a Spark image with Dockerfile (citing from Sergio)

We suppose to have a mesos cluster composed by 1 master and more slaves or 3 master in HA and more slaves. In this documentation we will explain how to create the Dockerfile that will be used by the Spark Driver and Spark Executor. For our example, we will consider that the Docker image should provide the CentOS7 distro along with additional Mesos and spark libraries. So, in a nutshell, the Docker image must have the following features:
 * The version of libmesos should be compatible with the version of the Mesos master and slave. For example, /usr/lib/libmesos-0.26.0.so
 * It should have a valid JDK
 * It should have the Python packages
 * It should have a version of Spark, we will choose 2.1.0
 * It should have the hadoop libraries.

#### Important configuration file and script

Let’s explain some very important files that will be available in the Docker image according to the Dockerfile mentioned earlier:

The spark-conf/spark-env.sh, as mentioned in the Spark docs, will be used to set the location of the Mesos libmesos.so:

```
export MESOSNATIVEJAVALIBRARY=${MESOSNATIVEJAVALIBRARY:-/usr/lib/libmesos.so}export SPARKLOCALIP=${SPARKLOCALIP:-"127.0.0.1"}export SPARKPUBLICDNS=${SPARKPUBLICDNS:-"127.0.0.1"}
```

The spark-conf/spark-defaults.conf serves as the definition of the default configuration for our Spark jobs within the container, the contents are as follows:

```
spark.master  SPARKMASTER
spark.mesos.mesosExecutor.cores   MESOSEXECUTORCORE
spark.mesos.executor.docker.image SPARKIMAGE
spark.mesos.executor.home /opt/spark
spark.driver.host CURRENTIP
spark.executor.extraClassPath /opt/spark/custom/lib/*
spark.driver.extraClassPath   /opt/spark/custom/lib/*
```

Note that the use of environment variables such as SPARKMASTER and SPARKIMAGE are critical since this will allow us to customize how the Spark application interacts with the Mesos Docker integration.

We have Docker's entry point script. The script, showcased below, will populate the spark-defaults.conf file.

Now, let’s define the Dockerfile entry point such that it lets us define some basic options that will get passed to the Spark command, for example, spark-shell, spark-submit or pyspark (script/RUN.sh)

#### Build the Docker