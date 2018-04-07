export MESOS_NATIVE_JAVA_LIBRARY=${MESOS_NATIVE_JAVA_LIBRARY:-/usr/lib/libmesos.so}
export SPARK_LOCAL_IP=${SPARK_LOCAL_IP:-"127.0.0.1"}
export SPARK_PUBLICDNS=${SPARK_PUBLIC_DNS:-"127.0.0.1"}
export LIBPROCESS_IP=${SPARK_LOCAL_IP:-"127.0.0.1"}
export JAVA_HOME=/opt/jdk

export LD_LIBRARY_PATH=/opt/hadoop/lib/native/:$LD_LIBRARY_PATH

export JAVA_OPTS_ERROR_HANDLING="-XX:ErrorFile=/tmp/spark-shell-hs_err_pid.log \
-XX:HeapDumpPath=/tmp/spark-shell-java_pid.hprof \
-XX:-HeapDumpOnOutOfMemoryError"


export JAVA_OPTS_GC="-XX:-PrintGC -XX:-PrintGCDetails \
-XX:-PrintGCTimeStamps \
-XX:-PrintTenuringDistribution \
-XX:-PrintAdaptiveSizePolicy \
-XX:GCLogFileSize=1024K \
-XX:-UseGCLogFileRotation \
-Xloggc:/tmp/spark-shell-gc.log \
-XX:+UseConcMarkSweepGC"

export JAVA_OPTS="$JAVA_OPTS_ERROR_HANDLING $JAVA_OPTS_GC"

export HADOOP_HOME="/opt/hadoop"

export HADOOP_CONF_DIR="$HADOOP_HOME/etc/hadoop"
export SPARK_YARN_USER_ENV="JAVA_HOME=/opt/jdk"
export SPARK_LOCAL_IP=$SPARKLOCALIP
