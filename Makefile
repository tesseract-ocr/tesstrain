export

## Make sure that sort always uses the same sort order.
LC_ALL := C

SHELL := /bin/bash
LOCAL := $(PWD)/usr
PATH := $(LOCAL)/bin:$(PATH)

# Path to the .traineddata directory with traineddata suitable for training 
# (for example from tesseract-ocr/tessdata_best). Default: $(LOCAL)/share/tessdata
TESSDATA =  $(LOCAL)/share/tessdata

# Name of the model to be built. Default: $(MODEL_NAME)
MODEL_NAME = foo

# Output directory for generated files. Default: $(OUTPUT_DIR)
OUTPUT_DIR = data/$(MODEL_NAME)

# Wordlist file for Dictionary dawg. Default: $(WORDLIST_FILE)
WORDLIST_FILE := $(OUTPUT_DIR)/$(MODEL_NAME).wordlist

# Numbers file for number patterns dawg. Default: $(NUMBERS_FILE)
NUMBERS_FILE := $(OUTPUT_DIR)/$(MODEL_NAME).numbers

# Punc file for Punctuation dawg. Default: $(PUNC_FILE)
PUNC_FILE := $(OUTPUT_DIR)/$(MODEL_NAME).punc

# Name of the model to continue from. Default: '$(START_MODEL)'
START_MODEL =

LAST_CHECKPOINT := $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE)_checkpoint

# Name of the proto model. Default: '$(PROTO_MODEL)'
PROTO_MODEL = $(OUTPUT_DIR)/$(MODEL_NAME).traineddata

# No of cores to use for compiling leptonica/tesseract. Default: $(CORES)
CORES = 4

# Leptonica version. Default: $(LEPTONICA_VERSION)
LEPTONICA_VERSION := 1.78.0

# Tesseract commit. Default: $(TESSERACT_VERSION)
TESSERACT_VERSION := 4.1.0

# Tesseract model repo to use. Default: $(TESSDATA_REPO)
TESSDATA_REPO = _best

# Ground truth directory. Default: $(GROUND_TRUTH_DIR)
GROUND_TRUTH_DIR := $(OUTPUT_DIR)-ground-truth

# Max iterations. Default: $(MAX_ITERATIONS)
MAX_ITERATIONS := 10000

# Network specification. Default: $(NET_SPEC)
NET_SPEC := [1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c\#\#\#]

# Index for Layer to be replaced. Default: $(LAYER_APPEND_INDEX)
LAYER_APPEND_INDEX := 5

# Replace Layer Network specification. Default: $(LAYER_NET_SPEC)
LAYER_NET_SPEC := [Lfx192 O1c1]

# Training Build Type - Impact, Plus, Layer or Scratch. Default: '$(BUILD_TYPE)'
BUILD_TYPE := Scratch

# Language Type - Indic, RTL or blank. Default: '$(LANG_TYPE)'
LANG_TYPE ?=

# Normalization mode - 2, 1 - for unicharset_extractor and Pass through Recoder for combine_lang_model
ifeq ($(LANG_TYPE),Indic)
	NORM_MODE =2
	RECODER =--pass_through_recoder
else
ifeq ($(LANG_TYPE),RTL)
	NORM_MODE =3
	RECODER =--pass_through_recoder --lang_is_rtl
else
	NORM_MODE =1
	RECODER=
endif
endif

# Page segmentation mode. Default: $(PSM)
PSM = 6

# Random seed for shuffling of the training data. Default: $(RANDOM_SEED)
RANDOM_SEED := 0

# Ratio of train / eval training data. Default: $(RATIO_TRAIN)
RATIO_TRAIN := 0.90

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    unicharset       Create unicharset"
	@echo "    lists            Create lists of lstmf filenames for training and eval"
	@echo "    training         Start training"
	@echo "    traineddata      Create best and fast .traineddata files from each .checkpoint file"
	@echo "    proto-model      Build the proto model"
	@echo "    leptonica        Build leptonica"
	@echo "    tesseract        Build tesseract"
	@echo "    tesseract-langs  Download tesseract-langs"
	@echo "    clean            Clean all generated files"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    MODEL_NAME         Name of the model to be built. Default: $(MODEL_NAME)"
	@echo "    START_MODEL        Name of the model to continue from. Default: '$(START_MODEL)'"
	@echo "    PROTO_MODEL        Name of the proto model. Default: '$(PROTO_MODEL)'"
	@echo "    CORES              No of cores to use for compiling leptonica/tesseract. Default: $(CORES)"
	@echo "    LEPTONICA_VERSION  Leptonica version. Default: $(LEPTONICA_VERSION)"
	@echo "    TESSERACT_VERSION  Tesseract commit. Default: $(TESSERACT_VERSION)"
	@echo "    TESSDATA_REPO      Tesseract model repo to use. Default: $(TESSDATA_REPO)"
	@echo "    TESSDATA           Path to the .traineddata directory to start finetuning from. Default: $(LOCAL)/share/tessdata"
	@echo "    GROUND_TRUTH_DIR   Ground truth directory. Default: $(GROUND_TRUTH_DIR)"
	@echo "    OUTPUT_DIR         Output directory for generated files. Default: $(OUTPUT_DIR)"
	@echo "    MAX_ITERATIONS     Max iterations. Default: $(MAX_ITERATIONS)"
	@echo "    NET_SPEC           Network specification. Default: $(NET_SPEC)"
	@echo "    LAYER_NET_SPEC     Replace Layer Network specification. Default: $(LAYER_NET_SPEC)"
	@echo "    LAYER_APPEND_INDEX Index for Layer to be replaced. Default: $(LAYER_APPEND_INDEX)"
	@echo "    BUILD_TYPE         Training Type - Impact, Plus, Layer or Scratch. Default: '$(BUILD_TYPE)'"
	@echo "    LANG_TYPE          Language Type - Indic, RTL or blank. Default: '$(LANG_TYPE)'"
	@echo "    PSM                Page segmentation mode. Default: $(PSM)"
	@echo "    RANDOM_SEED        Random seed for shuffling of the training data. Default: $(RANDOM_SEED)"
	@echo "    RATIO_TRAIN        Ratio of train / eval training data. Default: $(RATIO_TRAIN)"

# END-EVAL

.PHONY: clean help leptonica lists proto-model tesseract tesseract-langs training unicharset

.PRECIOUS: $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE)_checkpoint $(GROUND_TRUTH_DIR)/%.box $(GROUND_TRUTH_DIR)/%.lstmf

ALL_BOXES = $(OUTPUT_DIR)/all-boxes
ALL_LSTMF = $(OUTPUT_DIR)/all-lstmf

# Create unicharset
unicharset: $(OUTPUT_DIR)/unicharset

# Create lists of lstmf filenames for training and eval
lists: $(OUTPUT_DIR)/list.train $(OUTPUT_DIR)/list.eval

$(OUTPUT_DIR)/list.eval \
$(OUTPUT_DIR)/list.train: $(ALL_LSTMF)
	@mkdir -p $(OUTPUT_DIR)
	@total=$$(wc -l < $(ALL_LSTMF)); \
	  train=$$(echo "$$total * $(RATIO_TRAIN) / 1" | bc); \
	  test "$$train" = "0" && \
	    echo "Error: missing ground truth for training" && exit 1; \
	  eval=$$(echo "$$total - $$train" | bc); \
	  test "$$eval" = "0" && \
	    echo "Error: missing ground truth for evaluation" && exit 1; \
	  set -x; \
	  head -n "$$train" $(ALL_LSTMF) > "$(OUTPUT_DIR)/list.train"; \
	  tail -n "$$eval" $(ALL_LSTMF) > "$(OUTPUT_DIR)/list.eval"

# Start training
training: $(OUTPUT_DIR)$(BUILD_TYPE).traineddata

ifdef START_MODEL
$(OUTPUT_DIR)/unicharset: $(ALL_BOXES)
	@mkdir -p data/$(START_MODEL)
	combine_tessdata -u $(TESSDATA)/$(START_MODEL).traineddata  data/$(START_MODEL)/$(MODEL_NAME)
	unicharset_extractor --output_unicharset "$(GROUND_TRUTH_DIR)/my.unicharset" --norm_mode $(NORM_MODE) "$(ALL_BOXES)"
	merge_unicharsets data/$(START_MODEL)/$(MODEL_NAME).lstm-unicharset $(GROUND_TRUTH_DIR)/my.unicharset  "$@"
else
$(OUTPUT_DIR)/unicharset: $(ALL_BOXES)
	@mkdir -p $(OUTPUT_DIR)
	unicharset_extractor --output_unicharset "$@" --norm_mode 1 "$(ALL_BOXES)"
endif

$(ALL_BOXES): $(patsubst %.tif,%.box,$(shell find $(GROUND_TRUTH_DIR) -name '*.tif'))
	@mkdir -p $(OUTPUT_DIR)
	find $(GROUND_TRUTH_DIR) -name '*.box' | xargs cat | sort | uniq > "$@"

%.box: %.tif %.gt.txt
	PYTHONIOENCODING=utf-8 python3 generate_line_box.py -i "$*.tif" -t "$*.gt.txt" > "$@"

$(ALL_LSTMF): $(patsubst %.tif,%.lstmf,$(shell find $(GROUND_TRUTH_DIR) -name '*.tif'))
	@mkdir -p $(OUTPUT_DIR)
                                                                                                                                                                  
	find $(GROUND_TRUTH_DIR) -name '*.lstmf' | python3 shuffle.py $(RANDOM_SEED) > "$@"

%.lstmf: %.box
	tesseract $*.tif $* --psm $(PSM) lstm.train

# Create best and fast .traineddata files from each .checkpoint file
CHECKPOINT_FILES := $(wildcard $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)*.checkpoint)
.PHONY: traineddata
traineddata: $(OUTPUT_DIR)/tessdata_best $(OUTPUT_DIR)/tessdata_fast
traineddata: $(subst checkpoints,tessdata_best,$(patsubst %.checkpoint,%.traineddata,$(CHECKPOINT_FILES)))
traineddata: $(subst checkpoints,tessdata_fast,$(patsubst %.checkpoint,%.traineddata,$(CHECKPOINT_FILES)))
$(OUTPUT_DIR)/tessdata_best $(OUTPUT_DIR)/tessdata_fast:
	mkdir $@
$(OUTPUT_DIR)/tessdata_best/%.traineddata: $(OUTPUT_DIR)/checkpoints/%.checkpoint
	lstmtraining \
          --stop_training \
          --continue_from $< \
          --traineddata $(PROTO_MODEL) \
          --model_output $@
$(OUTPUT_DIR)/tessdata_fast/%.traineddata: $(OUTPUT_DIR)/checkpoints/%.checkpoint
	lstmtraining \
          --stop_training \
          --continue_from $< \
          --traineddata $(PROTO_MODEL) \
          --convert_to_int \
          --model_output $@

# Build the proto model
proto-model: $(PROTO_MODEL)

$(PROTO_MODEL): $(OUTPUT_DIR)/unicharset data/radical-stroke.txt
	combine_lang_model \
	  --input_unicharset $(OUTPUT_DIR)/unicharset \
	  --script_dir data \
	  --numbers $(NUMBERS_FILE) \
	  --puncs $(PUNC_FILE) \
	  --words $(WORDLIST_FILE) \
	  --output_dir data \
	  $(RECODER) \
	  --lang $(MODEL_NAME)

ifdef START_MODEL
ifeq ($(BUILD_TYPE),Impact)
$(LAST_CHECKPOINT): unicharset lists
	mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(TESSDATA)/$(START_MODEL).traineddata \
	  --continue_from data/$(START_MODEL)/$(MODEL_NAME).lstm \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE) \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --max_iterations $(MAX_ITERATIONS)
	lstmeval \
	  --traineddata $(TESSDATA)/$(START_MODEL).traineddata \
	  --model $(LAST_CHECKPOINT) \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
	lstmeval \
	  --model $(TESSDATA)/$(START_MODEL).traineddata \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(TESSDATA)/$(START_MODEL).traineddata \
	--model_output $@
endif
ifeq ($(BUILD_TYPE),Plus)
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	@mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --old_traineddata $(TESSDATA)/$(START_MODEL).traineddata \
	  --continue_from data/$(START_MODEL)/$(MODEL_NAME).lstm \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE) \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --max_iterations $(MAX_ITERATIONS)
	lstmeval \
	  --traineddata $(PROTO_MODEL) \
	  --model $(LAST_CHECKPOINT) \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
	lstmeval \
	  --model $(TESSDATA)/$(START_MODEL).traineddata \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
endif
ifeq ($(BUILD_TYPE),Layer)
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --append_index $(LAYER_APPEND_INDEX) --net_spec '$(LAYER_NET_SPEC)' \
	  --continue_from data/$(START_MODEL)/$(MODEL_NAME).lstm \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE) \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --max_iterations $(MAX_ITERATIONS)
	lstmeval \
	  --traineddata $(PROTO_MODEL) \
	  --model $(LAST_CHECKPOINT) \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
	lstmeval \
	  --model $(TESSDATA)/$(START_MODEL).traineddata \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
endif
else
ifeq ($(BUILD_TYPE),Scratch)
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	@mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --net_spec "$(subst c###,c`head -n1 $(OUTPUT_DIR)/unicharset`,$(NET_SPEC))" \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE) \
	  --learning_rate 20e-4 \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --max_iterations $(MAX_ITERATIONS)
	lstmeval \
	  --traineddata $(PROTO_MODEL) \
	  --model $(LAST_CHECKPOINT) \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
endif
endif

data/radical-stroke.txt:
	wget -O$@ 'https://github.com/tesseract-ocr/langdata_lstm/raw/master/radical-stroke.txt'

# Build leptonica
leptonica: leptonica.built

leptonica.built: leptonica-$(LEPTONICA_VERSION)
	cd $< ; \
		./configure --prefix=$(LOCAL) && \
		make -j$(CORES) && \
		make install && \
		date > "$@"

leptonica-$(LEPTONICA_VERSION): leptonica-$(LEPTONICA_VERSION).tar.gz
	tar xf "$<"

leptonica-$(LEPTONICA_VERSION).tar.gz:
	wget 'http://www.leptonica.org/source/$@'

# Build tesseract
tesseract: tesseract.built tesseract-langs

tesseract.built: tesseract-$(TESSERACT_VERSION)
	cd $< && \
		sh autogen.sh && \
		PKG_CONFIG_PATH="$(LOCAL)/lib/pkgconfig" \
			./configure --prefix=$(LOCAL) && \
		LDFLAGS="-L$(LOCAL)/lib"\
			make -j$(CORES) install training-install && \
		date > "$@"

tesseract-$(TESSERACT_VERSION):
	wget https://github.com/tesseract-ocr/tesseract/archive/$(TESSERACT_VERSION).zip
	unzip $(TESSERACT_VERSION).zip

# Download tesseract-langs
tesseract-langs: $(TESSDATA)/eng.traineddata

$(TESSDATA)/eng.traineddata:
	cd $(TESSDATA) && wget https://github.com/tesseract-ocr/tessdata$(TESSDATA_REPO)/raw/master/$(notdir $@)

# Clean all generated files
clean:
	find $(GROUND_TRUTH_DIR) -name '*.box' -delete
	find $(GROUND_TRUTH_DIR) -name '*.lstmf' -delete
	rm -rf $(OUTPUT_DIR)
