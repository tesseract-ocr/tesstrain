SHELL := /bin/bash

MODEL_NAME = foo

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    unicharset  Create unicharset"
	@echo "    lists       Create lists of lstmf filenames for training and eval"
	@echo "    training    Start training"
	@echo "    clean       Clean all generated files"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    TRAIN        Train directory"
	@echo "    RATIO_EVAL   Ratio of train / eval training data"
	@echo "    BOX_FILES    Box files"
	@echo "    LSTMF_FILES  lstmf files"

# END-EVAL

# Train directory
TRAIN := data/train

# Ratio of train / eval training data
RATIO_TRAIN := 0.9
RATIO_EVAL := $(shell echo "1.0 - $(RATIO_TRAIN)"|bc)

# Box files
BOX_FILES = $(shell find data/train -name '*.tif' |sed 's,\.tif,.box,')

# lstmf files
LSTMF_FILES = $(shell find data/train -name '*.tif' |sed 's,\.tif,.lstmf,')

ALL_BOXES = data/all-boxes
ALL_LSTMF = data/all-lstmf

# Create unicharset
unicharset: data/unicharset

# Create lists of lstmf filenames for training and eval
lists: $(ALL_LSTMF)
	no=`cat $(ALL_LSTMF) | wc -l` \
	   no_train=`echo "$$no * $(RATIO_TRAIN) / 1" | bc` \
	   no_eval=`echo "$$no * $(RATIO_EVAL) / 1" | bc`; \
	   head -n "$$no_train" $(ALL_LSTMF) > data/list.train; \
	   head -n "$$no_eval" $(ALL_LSTMF) > data/list.eval;

# Start training
training: data/$(MODEL_NAME).traineddata

data/unicharset: $(ALL_BOXES)
	unicharset_extractor --output_unicharset "$@" --norm_mode 1 "$(ALL_BOXES)"

$(ALL_BOXES): $(BOX_FILES)
	find $(TRAIN) -name '*.box' -exec cat {} \; > "$@"

$(TRAIN)/%.box: $(TRAIN)/%.tif $(TRAIN)/%.gt.txt
	python generate_line_box.py -i "$(TRAIN)/$*.tif" -t "$(TRAIN)/$*.gt.txt" > "$@"

$(ALL_LSTMF): $(LSTMF_FILES)
	find $(TRAIN) -name '*.lstmf' -exec echo {} \; | sort -R -o "$@"

$(TRAIN)/%.lstmf: $(TRAIN)/%.box
	tesseract $(TRAIN)/$*.tif $(TRAIN)/$* lstm.train

radical-stroke.txt:
	wget 'https://raw.githubusercontent.com/tesseract-ocr/langdata/master/radical-stroke.txt'

proto-model: data/$(MODEL_NAME)/$(MODEL_NAME).traineddata

data/$(MODEL_NAME)/$(MODEL_NAME).traineddata: radical-stroke.txt data/unicharset
	combine_lang_model \
	  --input_unicharset data/unicharset \
	  --script_dir . \
	  --output_dir data/ \
	  --lang $(MODEL_NAME)

data/checkpoints/$(MODEL_NAME)_checkpoint: data/unicharset data/list.eval data/list.train
	mkdir -p data/checkpoints
	lstmtraining \
	  --traineddata data/$(MODEL_NAME)/$(MODEL_NAME).traineddata \
	  --net_spec "[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c`head -n1 data/unicharset`]" \
	  --model_output data/checkpoints/$(MODEL_NAME) \
	  --learning_rate 20e-4 \
	  --train_listfile data/list.train \
	  --eval_listfile data/list.eval \
	  --max_iterations 10000

data/$(MODEL_NAME).traineddata: data/checkpoints/$(MODEL_NAME)_checkpoint
	lstmtraining \
	--stop_training \
	--continue_from $^ \
	--traineddata data/$(MODEL_NAME)/$(MODEL_NAME).traineddata \
	--model_output $@

# Clean all generated files
clean:
	rm -rf data/train/*.box
	rm -rf data/train/*.lstmf
	rm -rf data/all-*
	rm -rf data/list.*
	rm -rf data/$(MODEL_NAME)
	rm -rf data/unicharset
	rm -rf data/checkpoints
