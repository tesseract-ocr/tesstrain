#!/bin/bash
# `make` needs to be run twice, 
# first to generate traineddata and then to generate new validate.log files.
# $1 - lang code of START_MODEL = TESSTRAIN_LANG
# $2 - maximum CER for y axis - adjust based on graph

cd plot
make MODEL_NAME=$1 VALIDATE_LIST=eval Y_MAX_CER=$2
make MODEL_NAME=$1 VALIDATE_LIST=eval Y_MAX_CER=$2
