B# Docker

1. [How to create the container](#How-to-create-the-container)
   * [Install Docker in your host](#install-docker-in-your-host)
   * [Creating a Spark image with Dockerfile](#Creating-a-Spark-image-with-Dockerfile)
   * [Important conf file and script](#Important-conf-file-and-script)
   * [Build the Docker](#Build-the-Docker)
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

### Creating a Spark image with Dockerfile
