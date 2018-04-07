#!/bin/bash
IMAGE="siewyanhoh/shohmesos:v3"

#attact to ttyl
#docker run -it -e SPARK_MASTER=mesos://10.64.22.90:5050 -e SPARK_IMAGE=$IMAGE --name $1 --net host --privileged --pid host $IMAGE /opt/spark/bin/spark-shell --master mesos://10.64.22.90:5050

#spark-submit
#docker run -it --rm \
#    -v /root/Zpeak_nano_multipledataset.py:/root/Zpeak_nano_multipledataset.py \
#    -v /root/samples.py:/root/samples.py \
#    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
#    -e SPARK_IMAGE=$IMAGE \
#    --net host --privileged --pid host $IMAGE \
#    /opt/spark/bin/spark-submit \
#    --master mesos://10.64.22.90:5050 \
#    --name $1 \
#    --conf "spark.jars.packages=org.diana-hep:spark-root_2.11:0.1.16,org.diana-hep:histogrammar-sparksql_2.11:1.0.4" \
#    --conf "spark.driver.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
#    --conf "spark.executor.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
#    --conf "spark.deploy.defaultCores=8" \
#    --conf "spark.executor.memory=4g" \
#    --conf "spark.driver.supervise=true" \
#    /root/Zpeak_nano_multipledataset.py

# Run on a Mesos cluster in cluster deploy mode with supervise
docker run -it --rm -e SPARK_MASTER=mesos://10.64.22.90:5050 -e SPARK_IMAGE=$IMAGE \
    --net host --privileged --pid host $IMAGE \
    /opt/spark/bin/spark-submit \
    --class org.apache.spark.examples.SparkPi \
    --master mesos://10.64.22.90:5050 \
    --executor-memory 1G \
    --total-executor-cores 1 \
    /opt/spark/examples/jars/spark-examples_2.11-2.2.1.jar \
    1000
