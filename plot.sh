#!/bin/bash
# `make` needs to be run twice, 
# first to generate traineddata and then to generate new validate.log files.
# $1 - MODEL_NAME
# $2 - VALIDATE_LIST
# $3 - maximum CER for y axis - adjust based on graph

cd plot
make MODEL_NAME=$1 VALIDATE_LIST=$2 Y_MAX_CER=$3
make MODEL_NAME=$1 VALIDATE_LIST=$2 Y_MAX_CER=$3
