#!/bin/bash
## bash -x EVAL-VALIDATE-PLOT.sh validate
## Do not run validate on list.eval, since that is already reflected in MODEL_LOG.

MODEL_NAME=sanPlusMinus
VALIDATIONLIST=$1
MAXCER=9 # MAXCER should be between 0-9 - will select checkpoints till MAXCER.9*
VALIDATIONLOG=plot/${MODEL_NAME}-fast${VALIDATIONLIST}.log
MODEL_LOG=plot/${MODEL_NAME}.LOG

## make all traineddata files
make traineddata MODEL_NAME=${MODEL_NAME}  

## run eval against validate list with the best CER models (%range as in Makefile-Validate)
make -f Makefile-Validate fasteval MODEL_NAME=${MODEL_NAME} VALIDATIONLIST=${VALIDATIONLIST} MAXCER=${MAXCER}

## PLOT the LOGS

grep 'best model' ${MODEL_LOG} |  sed  -e 's/^.*\///' |  sed  -e 's/\.checkpoint.*$/\t\t\t/' | sed  -e 's/_/\t/g' > plot/tmp-${MODEL_NAME}-plot-best.tsv
grep 'Eval Char' ${MODEL_LOG} | sed -e 's/^.*[0-9]At iteration //' | \sed -e 's/,.* Eval Char error rate=/\t\t/'  | sed -e 's/, Word.*$/\t\t/' | sed -e 's/^/\t\t/'> plot/tmp-${MODEL_NAME}-plot-eval.tsv
grep 'At iteration' ${MODEL_LOG} |  sed -e '/^Sub/d' |  sed -e '/^Update/d' | sed  -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' |  sed  -e 's/%, word.*$/\t/'   > plot/tmp-${MODEL_NAME}-plot-iteration.tsv
egrep "${VALIDATIONLIST}.log$|iteration" ${VALIDATIONLOG} > plot/tmp-${MODEL_NAME}-plot-${MODEL_NAME}-${VALIDATIONLIST}.LOG
sed 'N;s/\nAt iteration 0, stage 0, /At iteration 0, stage 0, /;P;D'  plot/tmp-${MODEL_NAME}-plot-${MODEL_NAME}-${VALIDATIONLIST}.LOG | grep 'Eval Char' | sed -e "s/.${VALIDATIONLIST}.log.*Eval Char error rate=/\t\t\t/" | sed -e 's/, Word.*$//' | sed  -e 's/\(^.*\)_\([0-9].*\)_\([0-9].*\)_\([0-9].*\)\t/\1\t\2\t\3\t\4\t/g' >  plot/tmp-${MODEL_NAME}-plot-validation.tsv
echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > plot/tmp-${MODEL_NAME}-plot-header.tsv
cat plot/tmp-${MODEL_NAME}-plot-header.tsv  plot/tmp-${MODEL_NAME}-plot-iteration.tsv plot/tmp-${MODEL_NAME}-plot-best.tsv plot/tmp-${MODEL_NAME}-plot-eval.tsv    plot/tmp-${MODEL_NAME}-plot-validation.tsv  > plot/${MODEL_NAME}-${VALIDATIONLIST}-plot_cer.tsv

python EVAL-VALIDATE-PLOT.py -m ${MODEL_NAME} -v ${VALIDATIONLIST}

rm plot/tmp-${MODEL_NAME}-plot-*  
