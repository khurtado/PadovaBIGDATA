#!/bin/bash

if [ "${SPARK_HOME}" == "" ];then
    echo "SPARK is not installed in the cluster, exiting"
    exit 0
fi

WORKDIR=`pwd`
MASTER="spark://10.64.22.198:7077"

submit=1

if [ "${submit}" == 1 ];then
    #spark-submit in CLIENT MODE
    spark-submit \
	--master "${MASTER}" \
	--conf "spark.jars.packages=org.diana-hep:spark-root_2.11:0.1.16,org.diana-hep:histogrammar-sparksql_2.11:1.0.4,ch.cern.sparkmeasure:spark-measure_2.11:0.11" \
	--conf "spark.driver.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
	--conf "spark.executor.extraClassPath=/opt/hadoop/share/hadoop/common/lib/EOSfs.jar" \
	--conf "spark.num.executors=8" \
	--conf "spark.executor.cores=2" \
	--conf "spark.executor.memory=1g" \
	--conf "spark.executor.instances=4" \
	--conf "spark.history.ui.acls.enable=false" \
	--conf "spark.eventLog.enabled=true" \
	--conf "spark.eventLog.dir=hdfs://10.64.22.72:9000/eventLogging" \
	${WORKDIR}/../zpeak_keras.py
else
    #Running jupyter notebook in CLIENT MODE
    echo "Ensure ssh tunnel established at 11198"
    jupyter notebook --ip 127.0.0.1 --port 11198 --no-browser
fi
