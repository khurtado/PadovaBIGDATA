#!/bin/bash

echo "jupyter notebook --port $1 --ip 127.0.0.1 --allow-root"
jupyter notebook --port $1 --ip 127.0.0.1 --allow-root
