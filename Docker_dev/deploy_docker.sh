#!/bin/bash

#attact to ttyl
#docker run --rm -it -e SPARK_MASTER=mesos://10.64.22.90:5050 -e SPARK_IMAGE=$IMAGE --name "test" --net host --privileged --pid host $IMAGE /opt/spark/bin/spark-shell --master mesos://10.64.22.90:5050
#org.diana-hep:histogrammar-sparksql_2.11:1.0.4

#spark-submit in CLIENT MODE
docker run -it --rm \
    -v pyscript/zpeak.py:/root/zpeak.py \
    -v pyscript/samples.py:/root/samples.py \
    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
    -e SPARK_IMAGE=siewyanhoh/shohmesos:Spark221 \
    --net=host --pid host \
    siewyanhoh/shohmesos:Spark221 \
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
    /root/zpeak.py

#Running jupyter notebook in CLIENT MODE
docker run -it --rm \
    -v notebooks/Zpeak_nano_multipledataset.ipynb:/Zpeak_nano_multipledataset.ipynb \
    -v notebooks/DemonMl_Dist-Keras.ipynb:/DemonMl_Dist-Keras.ipynb \
    -v notebooks/samples.py:/samples.py \
    -v notebooks/Cache-test.ipynb:/Cache-test.ipynb \
    -e SPARK_MASTER=mesos://10.64.22.90:5050 \
    -e SPARK_IMAGE=siewyanhoh/shohmesos:Spark221 \
    -e SPARK_LOCAL_IP=10.64.22.90 \
    --net host --pid host \
    --privileged \
    -p 1190:1190 \
    siewyanhoh/shohmesos:Spark221 \
    /bin/bash -c 'source /opt/spark/conf/spark-env.sh;jupyter notebook --port 1190 --ip 0.0.0.0 --allow-root'
