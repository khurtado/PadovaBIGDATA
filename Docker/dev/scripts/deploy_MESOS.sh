#!/bin/bash

WORKDIR=`pwd`

MASTER="mesos://10.64.22.90:5050"

submit=1

if [ "${submit}" == 1 ];then
    #spark-submit in CLIENT MODE
    docker run -it --rm \
	-v ${WORKDIR}/../spark-submit/zpeak.py:/root/zpeak.py \
	-v ${WORKDIR}/../spark-submit/samples.py:/root/samples.py \
	-e SPARK_MASTER=${MASTER} \
	-e SPARK_IMAGE=siewyanhoh/shohmesos:v3.3 \
	--net=host --pid host \
	siewyanhoh/shohmesos:v3.3 \
	/opt/spark/bin/spark-submit \
	--master ${MASTER} \
	--conf "spark.jars.packages=org.diana-hep:spark-root_2.11:0.1.16,org.diana-hep:histogrammar-sparksql_2.11:1.0.4,ch.cern.sparkmeasure:spark-measure_2.11:0.11" \
	--conf "spark.driver.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
	--conf "spark.executor.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
	--conf "spark.driver.memory=2g" \
	--conf "spark.num.executors=8" \
	--conf "spark.executor.cores=2" \
	--conf "spark.executor.instances=4" \
	--conf "spark.executor.memory=2g" \
	/root/zpeak.py
else
    #Running jupyter notebook in CLIENT MODE
    docker run -it --rm \
	-v ${WORKDIR}/../notebooks/Zpeak_nano_multipledataset.ipynb:/Zpeak_nano_multipledataset.ipynb \
	-v ${WORKDIR}/../notebooks/DemonMl_Dist-Keras.ipynb:/DemonMl_Dist-Keras.ipynb \
	-v ${WORKDIR}/../notebooks/samples.py:/samples.py \
	-v ${WORKDIR}/../notebooks/Cache-test.ipynb:/Cache-test.ipynb \
	-e SPARK_MASTER=${MASTER} \
	-e SPARK_IMAGE=siewyanhoh/shohmesos:Spark221 \
	-e SPARK_LOCAL_IP=10.64.22.90 \
	--net host --pid host \
	--privileged \
	-p 1190:1190 \
	siewyanhoh/shohmesos:Spark221 \
	/bin/bash -c 'source /opt/spark/conf/spark-env.sh;jupyter notebook --port 1190 --ip 0.0.0.0 --allow-root'
fi
