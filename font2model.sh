#!/bin/bash
# $1 - TESSTRAIN_LANG
# $2 - TESSTRAIN_SCRIPT
# $3 - START_MODEL
# $4 - MODEL_NAME
# $5 - TRAIN_TYPE - FineTune, ReplaceLayer or blank (from scratch)
# $6 - TESSTRAIN_FONT
# $7 - TESSTRAIN_MAX_PAGES per font
##

# nohup bash -x font2model.sh eng Latin eng iast ReplaceLayer ' "Arial Unicode MS" "Times New Roman," ' 25 > iast.log &

rm -rf /tmp 
fc-cache -vf

shuf -o data/$4-train.training_text < data/$4.training_text
shuf -o data/$4-eval.training_text < data/EVAL.training_text

make -f Makefile-font2model \
MODEL_NAME=$4 \
clean-groundtruth \
clean-output \
clean-log

make -f Makefile-font2model \
TESSDATA=$HOME/tessdata_best \
TESSTRAIN_FONTS_DIR=/usr/share/fonts \
TESSTRAIN_TEXT=data/$4-train.training_text \
TESSEVAL_TEXT=data/$4-eval.training_text \
TESSTRAIN_MAX_PAGES=$7 \
MAX_ITERATIONS=1000000 \
TESSTRAIN_LANG=$1 \
TESSTRAIN_SCRIPT=$2 \
START_MODEL=$3 \
MODEL_NAME=$4 \
TRAIN_TYPE=$5 \
TESSTRAIN_FONT="$6" \
DEBUG_INTERVAL=-1 \
training  --trace
