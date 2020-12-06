#!/bin/bash

MODEL_NAME=sanPlusMinus
MODEL_LOG=plot/${MODEL_NAME}.LOG

## PLOT the LOGS

grep 'best model' ${MODEL_LOG} |  sed  -e 's/^.*\///' |  sed  -e 's/\.checkpoint.*$/\t\t\t/' | sed  -e 's/_/\t/g' > plot/tmp-${MODEL_NAME}-plot-best.tsv
grep 'Eval Char' ${MODEL_LOG} | sed -e 's/^.*[0-9]At iteration //' | \sed -e 's/,.* Eval Char error rate=/\t\t/'  | sed -e 's/, Word.*$/\t\t/' | sed -e 's/^/\t\t/'> plot/tmp-${MODEL_NAME}-plot-eval.tsv
grep 'At iteration' ${MODEL_LOG} |  sed -e '/^Sub/d' |  sed -e '/^Update/d' | sed  -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' |  sed  -e 's/%, word.*$/\t/'   > plot/tmp-${MODEL_NAME}-plot-iteration.tsv

echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > plot/tmp-${MODEL_NAME}-plot-header.tsv
cat plot/tmp-${MODEL_NAME}-plot-header.tsv  plot/tmp-${MODEL_NAME}-plot-iteration.tsv plot/tmp-${MODEL_NAME}-plot-best.tsv plot/tmp-${MODEL_NAME}-plot-eval.tsv  > plot/${MODEL_NAME}-plot_cer.tsv

python PLOT_CER.py -m ${MODEL_NAME} 

rm plot/tmp-${MODEL_NAME}-plot-*  
