MODEL_NAME = foo
VALIDATE_CER=9
VALIDATE_LIST=validate

MODEL_LOG = $(MODEL_NAME).LOG
FAST_VALIDATE_LOG = $(MODEL_NAME)-fast-$(VALIDATE_LIST).log
TMP_VALIDATE_LOG = tmp-$(MODEL_NAME)-$(VALIDATE_LIST).log

TMP_100_ITERATIONS = tmp-${MODEL_NAME}-plot-iteration.tsv
TMP_CHECKPOINT = tmp-${MODEL_NAME}-plot-checkpoint.tsv
TMP_EVAL = tmp-${MODEL_NAME}-plot-eval.tsv
TMP_HEADER = tmp-${MODEL_NAME}-plot-header.tsv
TMP_VALIDATE = tmp-${MODEL_NAME}-plot-validate.tsv

TSV_CER = ${MODEL_NAME}-plot_cer.tsv
TSV_VALIDATE_CER = ${MODEL_NAME}-${VALIDATE_LIST}-plot_cer.tsv

.PHONY: $(FAST_VALIDATE_LOG) $(TSV_CER) $(TMP_HEADER) $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL) $(TMP_VALIDATE) $(TSV_VALIDATE_CER) $(TMP_VALIDATE_LOG)

all: traineddata plotvalidatecer

traineddata:
	$(MAKE) -C ../ traineddata MODEL_NAME=$(MODEL_NAME)
	sed -i -e 's/^data/..\/data/' ../data/$(MODEL_NAME)/list.${VALIDATE_LIST}

plotvalidatecer: $(TSV_VALIDATE_CER)

FAST_DATA_FILES := $(shell find ../data/$(MODEL_NAME)/tessdata_fast/ -type f -name *_[0-$(VALIDATE_CER)].[0-9]*.traineddata | sort -n)
FAST_VALIDATE_LOG_FILES := $(subst tessdata_fast,tessdata_fast,$(patsubst %.traineddata,%.$(VALIDATE_LIST).log,$(FAST_DATA_FILES)))

$(TSV_VALIDATE_CER): $(TMP_VALIDATE) $(TSV_CER)
	cat $(TSV_CER) $(TMP_VALIDATE) > "$@"
	python plot-eval-validate-cer.py -m $(MODEL_NAME)  -v $(VALIDATE_LIST)
	rm $(TMP_VALIDATE) $(TMP_VALIDATE_LOG) $(FAST_VALIDATE_LOG)

$(TMP_VALIDATE): $(TMP_VALIDATE_LOG)
	sed 'N;s/\nAt iteration 0, stage 0, /At iteration 0, stage 0, /;P;D'  $(TMP_VALIDATE_LOG) \
		| grep 'Eval Char' \
		| sed -e "s/.$(VALIDATE_LIST).log.*Eval Char error rate=/\t\t\t/" \
		| sed -e 's/, Word.*$$//' \
		| sed -e 's/\(^.*\)_\([0-9].*\)_\([0-9].*\)_\([0-9].*\)\t/\1\t\2\t\3\t\4\t/g' >  "$@"

$(TMP_VALIDATE_LOG): $(FAST_VALIDATE_LOG)
	grep -E "$(VALIDATE_LIST).log$$|iteration" $(FAST_VALIDATE_LOG) > "$@"

$(FAST_VALIDATE_LOG): $(FAST_VALIDATE_LOG_FILES)
	cat $(FAST_VALIDATE_LOG_FILES) > $@

$(FAST_VALIDATE_LOG_FILES): %.$(VALIDATE_LIST).log: %.traineddata
	OMP_THREAD_LIMIT=1 lstmeval  \
    --verbosity=0 \
    --model $< \
    --eval_listfile ../data/$(MODEL_NAME)/list.${VALIDATE_LIST}    > $@ 2>&1

plotcer: $(TSV_CER)

$(TSV_CER): $(TMP_HEADER) $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL)
	cat $(TMP_HEADER) $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL)  > "$@"
	rm $(TMP_HEADER) $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL)
#	python plot-eval-cer.py -m $(MODEL_NAME)

$(TMP_HEADER):
	echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@"

$(TMP_100_ITERATIONS): $(MODEL_LOG)
	grep 'At iteration' $(MODEL_LOG) \
		| sed -e '/^Sub/d' \
		| sed -e '/^Update/d' \
		| sed -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' \
		| sed -e 's/%, word.*/\t/' >  "$@"

$(TMP_CHECKPOINT): $(MODEL_LOG)
	grep 'best model' $(MODEL_LOG) \
		| sed -e 's/^.*\///' \
		| sed -e 's/\.checkpoint.*$$/\t\t\t/' \
		| sed -e 's/_/\t/g' >  "$@"

$(TMP_EVAL): $(MODEL_LOG)
	grep 'Eval Char' $(MODEL_LOG) \
		| sed -e 's/^.*[0-9]At iteration //' \
		| sed -e 's/,.* Eval Char error rate=/\t\t/'  \
		| sed -e 's/, Word.*$$/\t\t/' \
		| sed -e 's/^/\t\t/' >  "$@"
