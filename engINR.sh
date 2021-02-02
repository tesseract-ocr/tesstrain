#!/bin/bash
# Check length of lines in training text. Long lines wrap and create multi-line tifs.
# $1 - TESSTRAIN_LANG
# $2 - TESSTRAIN_SCRIPT
# $3 - TESSTRAIN_FONT
# $4 - Training Type - FineTune, ReplaceLayer or blank (from scratch)
# $5 - START_MODEL
# $6 - MODEL_NAME
#################
# FineTune - TESSTRAIN_MAX_LINES=1000 EPOCHS=10 
# ReplaceLayer - TESSTRAIN_MAX_LINES=10000 EPOCHS=10
# Scratch - TESSTRAIN_MAX_LINES=50000 EPOCHS=10
# eg. bash -x engINR.sh eng Latin 'Arial' FineTune eng engINR
###
###make -f Makefile-font2model \
###MODEL_NAME=$6 \
###clean-groundtruth \
###clean-output \
###clean-log
###
make -f Makefile-font2model \
MODEL_NAME=$6 \
START_MODEL=$5 \
TESSDATA=$HOME/tessdata_best \
TESSTRAIN_FONT="$3" \
TESSTRAIN_LANG=$1 \
TESSTRAIN_SCRIPT=$2 \
TESSTRAIN_FONTS_DIR=$HOME/.fonts \
TESSTRAIN_TEXT=data/$6.training_text \
TESSTRAIN_MAX_LINES=1000 EPOCHS=10  \
DEBUG_INTERVAL=-1 \
TRAIN_TYPE=$4 \
training  --trace
