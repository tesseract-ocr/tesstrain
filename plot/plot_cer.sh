#!/bin/bash
PREFIX=$1
echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > tmp-plot-header.csv
grep 'best model' ${PREFIX}.LOG |  sed  -e 's/^.*\///' |  sed  -e 's/\.checkpoint.*$//' | sed  -e 's/_/\t/g' > tmp-plot-best.csv
grep 'Eval Char' ${PREFIX}.LOG | sed -e 's/^.*[0-9]At iteration //' | \sed -e 's/,.* Eval Char error rate=/\t\t/'  | sed -e 's/, Word.*$//' | sed -e 's/^/\t\t/'> tmp-plot-eval.csv
grep 'At iteration' ${PREFIX}.LOG |  sed -e '/^Sub/d' |  sed -e '/^Update/d' | sed  -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' |  sed  -e 's/%, word.*$//'   > tmp-plot-iteration.csv
# order of concatenation is important for the secondary x axis mapping
cat tmp-plot-header.csv  tmp-plot-iteration.csv tmp-plot-best.csv tmp-plot-eval.csv > plot_cer.csv
rm tmp-plot-*
python plot_cer_zoomin.py
python plot_cer_zoomout.py
python plot_cer.py
rm ${PREFIX}-plot*.png
rename "s/plot/${PREFIX}-plot/" plot_cer*.png

