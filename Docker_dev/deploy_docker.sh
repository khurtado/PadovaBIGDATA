#!/bin/bash
#IMAGE="siewyanhoh/shohmesos:v3.3"
IMAGE="siewyanhoh/shohmesos:v4"
#APP="Zpeak_nano_multipledataset.py"
APP="zpeak.py"

#attact to ttyl
#docker run --rm -it -e SPARK_MASTER=mesos://10.64.22.90:5050 -e SPARK_IMAGE=$IMAGE --name "test" --net host --privileged --pid host $IMAGE /opt/spark/bin/spark-shell --master mesos://10.64.22.90:5050
#org.diana-hep:histogrammar-sparksql_2.11:1.0.4

#spark-submit in CLIENT MODE
docker run -it --rm \
    -v /root/$APP:/root/$APP \
    -v /root/samples.py:/root/samples.py \
    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
    -e SPARK_IMAGE=$IMAGE \
    --net=host --pid host \
    $IMAGE \
    /opt/spark/bin/spark-submit \
    --master mesos://10.64.22.90:5050 \
    --conf "spark.jars.packages=org.diana-hep:spark-root_2.11:0.1.16,org.diana-hep:histogrammar-sparksql_2.11:1.0.4,ch.cern.sparkmeasure:spark-measure_2.11:0.11" \
    --conf "spark.driver.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
    --conf "spark.executor.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
    --conf "spark.num.executors=8" \
    --conf "spark.executor.cores=1" \
    --conf "spark.executor.memory=1g" \
    --conf "spark.history.ui.acls.enable=false" \
    --conf "spark.eventLog.enabled=true" \
    --conf "spark.eventLog.dir=hdfs://10.64.22.72:9000/eventLogging" \
    /root/$APP

####PI

#Run in Mesos cluster with client mode
#docker run --rm -it --net=host -e SPARK_MASTER=mesos://10.64.22.90:5050 -e SPARK_IMAGE=$IMAGE \
#    $IMAGE \
#    /opt/spark/bin/spark-submit \
#    --master mesos://10.64.22.90:5050/mesos \
#    --conf "spark.executor.memory=1g" \
#    --conf "spark.executor.cores=1" \
#    --conf "spark.mesos.executor.docker.image=$IMAGE" \
#    --class org.apache.spark.examples.SparkPi \
#    /opt/spark/examples/jars/spark-examples_2.11-2.2.1.jar \
#    1000

#Run in Mesos master with client mode 
#docker run --rm -it --net=host -e SPARK_MASTER=mesos://10.64.22.90:5050 -e SPARK_IMAGE=$IMAGE \
#    $IMAGE \
#    /opt/spark/bin/spark-submit \
#    --master mesos://10.64.22.90:5050 \
#    --conf "spark.executor.memory=1g" \
#    --conf "spark.executor.cores=1" \
#    --conf "spark.mesos.executor.docker.image=$IMAGE" \
#    /opt/spark/examples/src/main/python/pi.py

########################################
#Run in Mesos master with ML application
########################################
#jupyter
#docker run -it --rm \
#    -v /root/ML/ML_HEP_PD/HIGGS_TRAIN.ipynb:/root/HIGGS_TRAIN.ipynb \
#    -v /root/ML/ML_HEP_PD/HIGGS.h5:/root/HIGGS.h5 \
#    -v /root/Zpeak_nano_multipledataset.ipynb:/Zpeak_nano_multipledataset.ipynb \
#    -v /root/samples.py:/samples.py \
#    -v /root/ML/iml_tensorflow_keras_workshop/keras:/root/keras \
#    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
#    -e SPARK_IMAGE=siewyanhoh/shohmesos:v4 \
#    --net host --pid host \
#    --privileged \
#    siewyanhoh/shohmesos:v4 \
#    /bin/bash -c 'source /opt/spark/conf/spark-env.sh;sh /jupy.sh 1190'

#spark-submit
#docker run -it --rm \
#    -v /root/ML/ML_HEP_PD/HIGGS.h5:/root/HIGGS.h5 \
#    -v /root/ML/ML_HEP_PD/HIGGS_TRAIN.py:/root/HIGGS_TRAIN.py \
#    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
#    -e SPARK_IMAGE=siewyanhoh/shohmesos:v4 \
#    --net host --pid host \
#    --privileged \
#    siewyanhoh/shohmesos:v4 \
#    /opt/spark/bin/spark-submit \
#    --master mesos://10.64.22.90:5050 \
#    --conf "spark.executor.memory=2g" \
#    --conf "spark.executor.cores=2" \
#    --conf "spark.cores.max=6" \
#    /root/HIGGS_TRAIN.py

#Cluster mode Dispatcher
#docker run --rm -it --net=host \
#    -v /root/spark.conf:/etc/spark.conf:ro \
#    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
#    -e SPARK_IMAGE=siewyanhoh/shohmesos:v4 \
#    siewyanhoh/shohmesos:v4 \
#    /opt/spark/bin/spark-class \
#    org.apache.spark.deploy.mesos.MesosClusterDispatcher \
#    --master mesos://zk://10.64.22.90:2181/mesos \
#    --name spark \
#    --properties-file /etc/spark.conf
