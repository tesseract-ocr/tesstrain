#!/bin/bash
# cp  $1-TESSTRAIN.LOG TESSTRAIN.LOG

echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > tmp-plot-header.csv
grep 'best model' TESSTRAIN.LOG |  sed  -e 's/^.*\///' |  sed  -e 's/\.checkpoint.*$//' | sed  -e 's/_/\t/g' > tmp-plot-best.csv
grep 'Eval Char' TESSTRAIN.LOG | sed -e 's/^.*[0-9]At iteration //' | \sed -e 's/,.* Eval Char error rate=/\t\t/'  | sed -e 's/, Word.*$//' | sed -e 's/^/\t\t/'> tmp-plot-eval.csv
grep 'At iteration' TESSTRAIN.LOG |  sed -e '/^Sub/d' |  sed -e '/^Update/d' | sed  -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' |  sed  -e 's/%, word.*$//'   > tmp-plot-iteration.csv
# order of concatenation is important for the secondary x axis mapping
cat tmp-plot-header.csv  tmp-plot-iteration.csv tmp-plot-best.csv tmp-plot-eval.csv > plot_cer.csv
rm tmp-plot-*
python plot_cer_plus.py
python plot_cer.py
# mv plot_cer.png $1-plot_cer.png
# mv plot_cer_plus.png $1-plot_cer_plus.png
