#!/bin/bash
# Check length of lines in training text. Long lines wrap and create multi-line tifs.
# $1 - lang code of START_MODEL = TESSTRAIN_LANG
# $2 - name of script for TESSTRAIN_SCRIPT
# $3 - Font Name
# $4 - Training Type - FineTune, ReplaceLayer or blank (from scratch)

make -f Makefile-new \
MODEL_NAME=$1-$4 \
clean-groundtruth \
clean-output \
clean-log

make -f Makefile-new \
MODEL_NAME=$1-$4 \
START_MODEL=$1 \
TESSDATA=$HOME/tessdata_best \
TESSTRAIN_FONT="$3" \
TESSTRAIN_LANG=$1 \
TESSTRAIN_SCRIPT=$2 \
TESSTRAIN_FONTS_DIR=$HOME/.fonts \
TESSTRAIN_TEXT=$HOME/langdata_lstm/$1/$1.training_text \
TESSTRAIN_MAX_LINES=100 \
EPOCHS=30  DEBUG_INTERVAL=-1 \
TRAIN_TYPE=$4 \
training
