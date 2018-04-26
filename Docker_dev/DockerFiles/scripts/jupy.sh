#!/bin/bash

echo "jupyter notebook --port $1 --ip 0.0.0.0 --allow-root"
jupyter notebook --port $1 --ip 0.0.0.0 --allow-root
