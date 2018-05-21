#!/bin/bash

export JAVA_HOME=/opt/jdk
SPARK_MASTER=${SPARK_MASTER:-local}
MESOS_EXECUTOR_CORE=${MESOS_EXECUTOR_CORE:-0.1}
SPARK_IMAGE=${SPARK_IMAGE:-sparkmesos:lastet}
DOCKER_IP=$(hostname -i)
CURRENT_IP=${CURRENT_IP:-$DOCKER_IP}

sed -i 's;SPARK_MASTER;'$SPARK_MASTER';g' /opt/spark/conf/spark-defaults.conf
sed -i 's;MESOS_EXECUTOR_CORE;'$MESOS_EXECUTOR_CORE';g' /opt/spark/conf/spark-defaults.conf
sed -i 's;SPARK_IMAGE;'$SPARK_IMAGE';g' /opt/spark/conf/spark-defaults.conf
sed -i 's;SPARK_IMAGE;'$SPARK_IMAGE';g' /opt/spark/conf/docker.properties

sed -i 's;CURRENT_IP;'$CURRENT_IP';g' /opt/spark/conf/spark-defaults.conf

export SPARK_LOCAL_IP=${SPARK_LOCAL_IP:-${CURRENT_IP:-"127.0.0.1"}}
export SPARK_PUBLIC_DNS=${SPARK_PUBLIC_DNS:-${CURRENT_IP:-"127.0.0.1"}}


if [ $ADDITIONALVOLUMES ];
then
    echo "spark.mesos.executor.docker.volumes: $ADDITIONALVOLUMES" >> /opt/spark/conf/spark-defaults.conf
fi

exec "$@"
