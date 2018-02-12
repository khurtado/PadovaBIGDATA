# BIGDATA

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