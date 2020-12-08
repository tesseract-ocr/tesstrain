MODEL_NAME = sanPlusMinus
MODEL_LOG = $(MODEL_NAME).LOG
VALIDATE_CER=9
VALIDATE_LIST=validate
FAST_VALIDATE_LOG = $(MODEL_NAME)-fast-$(VALIDATE_LIST).log
FAST_DATA_FILES = $(sort $(wildcard ../data/$(MODEL_NAME)/tessdata_fast/*_[0-$(VALIDATE_CER)].[0-9]*.traineddata))
FAST_VALIDATE_LOG_FILES = $(subst tessdata_fast,tessdata_fast,$(patsubst %.traineddata,%.$(VALIDATE_LIST).log,$(FAST_DATA_FILES)))
VALIDATE_LOG = tmp-$(MODEL_NAME)-$(VALIDATE_LIST).log

TSV_100_ITERATIONS = tmp-${MODEL_NAME}-plot-iteration.tsv
TSV_CHECKPOINT = tmp-${MODEL_NAME}-plot-checkpoint.tsv
TSV_EVAL = tmp-${MODEL_NAME}-plot-eval.tsv
TSV_HEADER = tmp-${MODEL_NAME}-plot-header.tsv
TSV_VALIDATE = tmp-${MODEL_NAME}-plot-validate.tsv
TSV_CER = ${MODEL_NAME}-plot_cer.tsv
TSV_VALIDATE_CER = ${MODEL_NAME}-${VALIDATE_LIST}-plot_cer.tsv

.PHONY: $(FAST_VALIDATE_LOG) $(TSV_CER) $(TSV_HEADER) $(TSV_100_ITERATIONS) $(TSV_CHECKPOINT) $(TSV_EVAL) $(TSV_VALIDATE) $(TSV_VALIDATE_CER) $(VALIDATE_LOG)

all: traineddata fastevallog plotcer plotvalidatecer

plotvalidatecer: traineddata fastevallog $(TSV_VALIDATE_CER)

$(TSV_VALIDATE_CER): $(TSV_VALIDATE) $(TSV_CER)
	cat $(TSV_CER) $(TSV_VALIDATE) > "$@"
	python plot-eval-validate-cer.py -m $(MODEL_NAME)  -v $(VALIDATE_LIST)
	rm $(TSV_VALIDATE) $(VALIDATE_LOG) $(FAST_VALIDATE_LOG)

$(TSV_VALIDATE): $(VALIDATE_LOG)
	sed 'N;s/\nAt iteration 0, stage 0, /At iteration 0, stage 0, /;P;D'  $(VALIDATE_LOG) \
		| grep 'Eval Char' \
		| sed -e "s/.$(VALIDATE_LIST).log.*Eval Char error rate=/\t\t\t/" \
		| sed -e 's/, Word.*$$//' \
		| sed  -e 's/\(^.*\)_\([0-9].*\)_\([0-9].*\)_\([0-9].*\)\t/\1\t\2\t\3\t\4\t/g' >  "$@"

$(VALIDATE_LOG): $(FAST_VALIDATE_LOG)
	grep -E "$(VALIDATE_LIST).log$$|iteration" $(FAST_VALIDATE_LOG) > "$@"

fastevallog: traineddata $(FAST_VALIDATE_LOG)

$(FAST_VALIDATE_LOG): $(FAST_VALIDATE_LOG_FILES)
	for i in $^; do \
		echo Filename : "$$i";echo;cat "$$i"; \
	done > $@

$(FAST_VALIDATE_LOG_FILES): %.$(VALIDATE_LIST).log: %.traineddata
	echo "***** $< ****"
	OMP_THREAD_LIMIT=1 lstmeval  \
    --verbosity=0 \
    --model $< \
    --eval_listfile ../data/$(MODEL_NAME)/list.${VALIDATE_LIST}    > $@ 2>&1

traineddata:
	$(MAKE) -C ../ traineddata MODEL_NAME=$(MODEL_NAME)
	sed -i -e 's/^data/..\/data/' ../data/$(MODEL_NAME)/list.${VALIDATE_LIST}

plotcer: $(TSV_CER)

$(TSV_CER): $(TSV_HEADER) $(TSV_100_ITERATIONS) $(TSV_CHECKPOINT) $(TSV_EVAL)
	cat $(TSV_HEADER) $(TSV_100_ITERATIONS) $(TSV_CHECKPOINT) $(TSV_EVAL)  > "$@"
	rm $(TSV_HEADER) $(TSV_100_ITERATIONS) $(TSV_CHECKPOINT) $(TSV_EVAL)
	python plot-eval-cer.py -m $(MODEL_NAME)

$(TSV_HEADER):
	echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@"

$(TSV_100_ITERATIONS): $(MODEL_LOG)
	grep 'At iteration' $(MODEL_LOG) \
		|  sed -e '/^Sub/d' \
		|  sed -e '/^Update/d' \
		| sed  -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' \
		|  sed -e 's/%, word.*/\t/' >  "$@"

$(TSV_CHECKPOINT): $(MODEL_LOG)
	grep 'best model' $(MODEL_LOG) \
		| sed  -e 's/^.*\///' \
		| sed  -e 's/\.checkpoint.*$$/\t\t\t/' \
		| sed  -e 's/_/\t/g' >  "$@"

$(TSV_EVAL): $(MODEL_LOG)
	grep 'Eval Char' $(MODEL_LOG) \
		| sed -e 's/^.*[0-9]At iteration //' \
		| \sed -e 's/,.* Eval Char error rate=/\t\t/'  \
		| sed -e 's/, Word.*$$/\t\t/' \
		| sed -e 's/^/\t\t/' >  "$@"

