#!/bin/bash

image="shohmesos"

sudo docker build -t ${image}
sudo docker tag ${image}:v2 ${image}:v2
