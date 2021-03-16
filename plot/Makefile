# Name of the model to be evaluated. Default: $(MODEL_NAME)
MODEL_NAME = foo

# Suffix of list of lstmf files to be used as validation set e.g. list.validate. Default: $(VALIDATE_LIST)
VALIDATE_LIST=validate

# Integer part of maximum Validation CER, ONLY use values between 0-9. Default: $(VALIDATE_CER)
VALIDATE_CER=9

# Training log file. This should match logfile name from training. Default: $(MODEL_LOG)
MODEL_LOG =../data/$(MODEL_NAME).log

# Directory for plot and tsv files for the model.
PLOT_DIR =../data/$(MODEL_NAME)/plot

# TSV file with header, iteration, checkpoint, eval and validation CER. Default: $(TSV_VALIDATE_CER)
# Info only, not used for plotting.
TSV_VALIDATE_CER = $(PLOT_DIR)/$(MODEL_NAME)-$(VALIDATE_LIST)-cer.tsv

# Temporary files.
TMP_VALIDATE_LIST =  tmp-$(MODEL_NAME)-$(VALIDATE_LIST).list
TMP_FAST_LOG = tmp-$(MODEL_NAME)-$(VALIDATE_LIST)-fast.log
TMP_VALIDATE_LOG = tmp-$(MODEL_NAME)-$(VALIDATE_LIST).log
TMP_100_ITERATIONS = tmp-$(MODEL_NAME)-$(VALIDATE_LIST)-iteration.tsv
TMP_CHECKPOINT = tmp-$(MODEL_NAME)-$(VALIDATE_LIST)-checkpoint.tsv
TMP_EVAL = tmp-$(MODEL_NAME)-$(VALIDATE_LIST)-eval.tsv
TMP_VALIDATE = tmp-$(MODEL_NAME)-$(VALIDATE_LIST)-validate.tsv

all: traineddata plotvalidatecer

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    traineddata      Create best and fast .traineddata files from each .checkpoint file"
	@echo "    plotvalidatecer  Make plots from TSV files generated from training and eval logs"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    MODEL_NAME         Name of the model to be built. Default: $(MODEL_NAME)"
	@echo "    VALIDATE_LIST      Suffix of lstmf files list, use validate for list.validate. Default: $(VALIDATE_LIST)"
	@echo ""

# END-EVAL

.PHONY:  $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL) $(TMP_VALIDATE) $(TSV_VALIDATE_CER) $(TMP_VALIDATE_LOG) $(TMP_FAST_LOG)

# Rename checkpoints with one/two decimal digits to 3 decimal digts for correct sorting later.
# Run Makefile in main directory to create traineddata from all checkpoints.
# Add ../ to lstmf file names in validate list relative to plot subdirectory.
traineddata:
	@find ../data/$(MODEL_NAME)/checkpoints/ -regex ^.*$(MODEL_NAME)_[0-9]\.[0-9]_.*_.*.checkpoint -exec rename -v 's/(.[0-9])_/$${1}00_/' {} \;
	@find ../data/$(MODEL_NAME)/checkpoints/ -regex ^.*$(MODEL_NAME)_[0-9]*\.[0-9][0-9]_.*_.*.checkpoint -exec rename -v 's/(.[0-9][0-9])_/$${1}0_/' {} \;
	$(MAKE) -C ../ traineddata MODEL_NAME=$(MODEL_NAME)
	@mkdir -p $(PLOT_DIR)
	@cp ../data/$(MODEL_NAME)/list.${VALIDATE_LIST} $(TMP_VALIDATE_LIST)
	@sed -i -e 's/^data/..\/data/' $(TMP_VALIDATE_LIST)

plotvalidatecer: $(TMP_FAST_LOG) $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL) $(TMP_VALIDATE) $(TSV_VALIDATE_CER)

# Make TSV with CER at every 100 iterations.
$(TMP_100_ITERATIONS): $(MODEL_LOG)
	@echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@"
	@grep 'At iteration' $(MODEL_LOG) \
		| sed -e '/^Sub/d' \
		| sed -e '/^Update/d' \
		| sed -e '/^ New worst char/d' \
		| sed -e 's/At iteration \([0-9]*\)\/\([0-9]*\)\/.*char train=/\t\t\1\t\2\t\t/' \
		| sed -e 's/%, word.*/\t/' >>  "$@"

# Make TSV with Checkpoint CER.
$(TMP_CHECKPOINT): $(MODEL_LOG)
	@echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@"
	@grep 'best model' $(MODEL_LOG) \
		| sed -e 's/^.*\///' \
		| sed -e 's/\.checkpoint.*$$/\t\t\t/' \
		| sed -e 's/_/\t/g' >>  "$@"

# Make TSV with Eval CER.
$(TMP_EVAL): $(MODEL_LOG)
	@echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@"
	@grep 'Eval Char' $(MODEL_LOG) \
		| sed -e 's/^.*[0-9]At iteration //' \
		| sed -e 's/,.* Eval Char error rate=/\t\t/'  \
		| sed -e 's/, Word.*$$/\t\t/' \
		| sed -e 's/^/\t\t/' >>  "$@"

# Validation log is generated only when CER falls below $(VALIDATE_CER)].9, so check for file existence.
# Extract Filename and CER from Validate log for building Validate TSV file.
# Make TSV with Validate CER.
$(TMP_VALIDATE): $(TMP_FAST_LOG)
	@if [ ! -s $(TMP_FAST_LOG) ]; \
	then \
		echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@" ;\
	else \
		grep -E "$(VALIDATE_LIST).log$$|iteration" $(TMP_FAST_LOG) > $(TMP_VALIDATE_LOG) ;\
		echo "Name	CheckpointCER	LearningIteration	TrainingIteration	EvalCER	IterationCER	ValidationCER" > "$@" ;\
		sed 'N;s/\nAt iteration 0, stage 0, /At iteration 0, stage 0, /;P;D'  $(TMP_VALIDATE_LOG) \
			| grep 'Eval Char' \
			| sed -e "s/.$(VALIDATE_LIST).log.*Eval Char error rate=/\t\t\t/" \
			| sed -e 's/, Word.*$$//' \
			| sed -e 's/\(^.*\)_\([0-9].*\)_\([0-9].*\)_\([0-9].*\)\t/\1\t\2\t\3\t\4\t/g' >> "$@" ;\
	fi;

# Build fast traineddata file list with CER in range [0-VALIDATE_CER].[0-9].
FAST_DATA_FILES := $(shell find ../data/$(MODEL_NAME)/tessdata_fast/ -type f -name $(MODEL_NAME)_[0-$(VALIDATE_CER)].[0-9]*_*.traineddata | sort -n -r)

# Build validate log files list based on above traineddata list.
FAST_LOG_FILES := $(subst tessdata_fast,tessdata_fast,$(patsubst %.traineddata,%.$(VALIDATE_LIST).log,$(FAST_DATA_FILES)))

#Note: This does not find the new traineddata files from current run. 
#	Hence `make` needs to be run twice to generate new validate.log files.

$(FAST_LOG_FILES): %.$(VALIDATE_LIST).log: %.traineddata
	OMP_THREAD_LIMIT=1 time -p lstmeval  \
		--verbosity=0 \
		--model $< \
		--eval_listfile $(TMP_VALIDATE_LIST) 2>&1 | grep "^At iteration" > $@

# Concatenate all validate.log files along with their filenames so as to include iteration number for TSV.
$(TMP_FAST_LOG): $(FAST_LOG_FILES)
	@for i in $^; do \
		echo Filename : "$$i";echo;cat "$$i"; \
	done > $@

# Combine TSV files with all required CER values, generated from training log and validation logs. Plot.
$(TSV_VALIDATE_CER): $(TMP_FAST_LOG) $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL) $(TMP_VALIDATE) 
	@cat $(TMP_100_ITERATIONS) $(TMP_CHECKPOINT) $(TMP_EVAL) $(TMP_VALIDATE) > "$@"
	python plot-eval-validate-cer.py -m $(MODEL_NAME) -v $(VALIDATE_LIST) -y $(Y_MAX_CER)
	@rm tmp-$(MODEL_NAME)-$(VALIDATE_LIST)*.*
