B# Docker

1. [How to create the container](#How-to-create-the-container)
   * [Install Docker in your host](#install-docker-in-your-host)
   * [Creating a Spark image with Dockerfile](#Creating-a-Spark-image-with-Dockerfile)
   * [Important conf file and script](#Important-conf-file-and-script)
   * [Build the Docker](#Build-the-Docker)
2. [Use the Spark with Mesos](#Use-the-Spark-with-Mesos)
3. [Reference](#reference)

## How to create the container

### Install Docker in your host

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

### Creating a Spark image with Dockerfile 

[citing from Sergio](https://github.com/SiewYan/BigData/tree/master/centosSparkmesos#install-docker-in-your-host)

We suppose to have a mesos cluster composed by 1 master and more slaves or 3 master in HA and more slaves. In this documentation we will explain how to create the Dockerfile that will be used by the Spark Driver and Spark Executor. For our example, we will consider that the Docker image should provide the CentOS7 distro along with additional Mesos and spark libraries. So, in a nutshell, the Docker image must have the following features:
 * The version of libmesos should be compatible with the version of the Mesos master and slave. For example, /usr/lib/libmesos-0.26.0.so
 * It should have a valid JDK
 * It should have the Python packages
 * It should have a version of Spark, we will choose 2.1.0
 * It should have the hadoop libraries.

#### Important conf file and script

Let’s explain some very important files that will be available in the Docker image according to the Dockerfile mentioned earlier:

The ```spark-conf/spark-env.sh```, as mentioned in the Spark docs, will be used to set the location of the Mesos libmesos.so:

```
export MESOSNATIVEJAVALIBRARY=${MESOSNATIVEJAVALIBRARY:-/usr/lib/libmesos.so}
export SPARKLOCALIP=${SPARKLOCALIP:-"127.0.0.1"}
export SPARKPUBLICDNS=${SPARKPUBLICDNS:-"127.0.0.1"}
```

The ```spark-conf/spark-defaults.conf``` serves as the definition of the default configuration for our Spark jobs within the container, the contents are as follows:

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

Little definition:

"A Dockerfile is a simple text-file that contains a list of commands that the Docker client calls while creating an image. It's a simple way to automate the image creation process. The best part is that the commands you write in a Dockerfile are almost identical to their equivalent Linux commands. This means you don't really have to learn new syntax to create your own dockerfiles."

Sergio kindly prepared a child image in this folder.

The ```docker build``` command does the heavy-lifting of creating a Docker image from a ```Dockerfile```. The ```docker build``` command takes ```-t``` optional tag name and a location of the directory containing the ```Dockerfile```.

```
sudo docker build -t mysparkmesoshadoop .
sudo docker tag mysparkmesoshadoop:latest mysparkmesoshadoop:latest
```

The command should build the spark image, inspecting via ```sudo docker ps``` would reveal the built image.

## Use the Spark with Mesos

Executing below command would run the spark image:

```
sudo docker run -it -e SPARK_MASTER=mesos://10.64.22.79:5050 -e SPARK_IMAGE=mysparkmesoshadoop --name mySparkShell --net host --privileged --pid host mysparkmesoshadoop /opt/spark/bin/spark-shell --master mesos://10.64.22.79:5050
```

Where 10.64.22.79 is the host ip where master mesos is running. 5050 the default mesos port. straldi/sparkhdfsmesos is the containr we just crerate and upload to docker repository (straldi is my own repository you could create yours). mySparkShell is the name of the app in mesos. This following command /opt/spark/bin/spark-shell --master mesos://10.64.22.79:5050 is the real command executed.

A spark-shell will be opened.

## Reference

* [Mesos - Spark](https://spark.apache.org/docs/latest/running-on-mesos.html)
* [Docker](https://www.docker.com/)