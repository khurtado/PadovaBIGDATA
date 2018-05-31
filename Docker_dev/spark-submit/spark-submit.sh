#!/bin/bash

spark-submit \
    --master "spark://10.64.22.198:7077" \
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
    zpeak_keras.py
    #zpeak_keras.py
