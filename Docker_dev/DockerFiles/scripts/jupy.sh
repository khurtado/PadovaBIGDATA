#!/bin/bash

source /opt/spark/conf/spark-env.sh

echo "jupyter notebook --port $1 --ip 0.0.0.0 --allow-root"
jupyter notebook --port $1 --ip 0.0.0.0 --allow-root
