export

# Disable built-in suffix and implicit pattern rules (for software builds).
# This makes starting with a very large number of GT lines much faster.
MAKEFLAGS += -r

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

# Data directory for output files, proto model, start model, etc. Default: $(DATA_DIR)
DATA_DIR = data

# Data directory for langdata (downloaded from Tesseract langdata repo). Default: $(LANGDATA_DIR)
LANGDATA_DIR = $(DATA_DIR)/langdata

# Output directory for generated files. Default: $(OUTPUT_DIR)
OUTPUT_DIR = $(DATA_DIR)/$(MODEL_NAME)

# Ground truth directory. Default: $(GROUND_TRUTH_DIR)
GROUND_TRUTH_DIR := $(OUTPUT_DIR)-ground-truth

# Optional Wordlist file for Dictionary dawg. Default: $(WORDLIST_FILE)
WORDLIST_FILE := $(OUTPUT_DIR)/$(MODEL_NAME).wordlist

# Optional Numbers file for number patterns dawg. Default: $(NUMBERS_FILE)
NUMBERS_FILE := $(OUTPUT_DIR)/$(MODEL_NAME).numbers

# Optional Punc file for Punctuation dawg. Default: $(PUNC_FILE)
PUNC_FILE := $(OUTPUT_DIR)/$(MODEL_NAME).punc

# Name of the model to continue from. Default: '$(START_MODEL)'
START_MODEL =

LAST_CHECKPOINT = $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)_checkpoint

# Name of the proto model. Default: '$(PROTO_MODEL)'
PROTO_MODEL = $(OUTPUT_DIR)/$(MODEL_NAME).traineddata

# No of cores to use for compiling leptonica/tesseract. Default: $(CORES)
CORES = 4

# Leptonica version. Default: $(LEPTONICA_VERSION)
LEPTONICA_VERSION := 1.80.0

# Tesseract commit. Default: $(TESSERACT_VERSION)
TESSERACT_VERSION := 4.1.1

# Tesseract model repo to use. Default: $(TESSDATA_REPO)
TESSDATA_REPO = _best

# If EPOCHS is given, it is used to set MAX_ITERATIONS.
ifeq ($(EPOCHS),)
# Max iterations. Default: $(MAX_ITERATIONS)
MAX_ITERATIONS := 10000
else
MAX_ITERATIONS := -$(EPOCHS)
endif

# Debug Interval. Default:  $(DEBUG_INTERVAL)
DEBUG_INTERVAL := 0

# Learning rate. Default: $(LEARNING_RATE)
ifdef START_MODEL
LEARNING_RATE := 0.0001
else
LEARNING_RATE := 0.002
endif

# Network specification. Default: $(NET_SPEC)
NET_SPEC := [1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx192 O1c\#\#\#]

# Language Type - Indic, RTL or blank. Default: '$(LANG_TYPE)'
LANG_TYPE ?=

# Normalization mode - 2, 1 - for unicharset_extractor and Pass through Recoder for combine_lang_model
ifeq ($(LANG_TYPE),Indic)
	NORM_MODE =2
	RECODER =--pass_through_recoder
	GENERATE_BOX_SCRIPT =generate_wordstr_box.py
else
ifeq ($(LANG_TYPE),RTL)
	NORM_MODE =3
	RECODER =--pass_through_recoder --lang_is_rtl
	GENERATE_BOX_SCRIPT =generate_wordstr_box.py
else
	NORM_MODE =2
	RECODER=
	GENERATE_BOX_SCRIPT =generate_line_box.py
endif
endif

# Page segmentation mode. Default: $(PSM)
PSM = 13

# Random seed for shuffling of the training data. Default: $(RANDOM_SEED)
RANDOM_SEED := 0

# Ratio of train / eval training data. Default: $(RATIO_TRAIN)
RATIO_TRAIN := 0.90

# Default Target Error Rate. Default: $(TARGET_ERROR_RATE)
TARGET_ERROR_RATE := 0.01

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    unicharset       Create unicharset"
	@echo "    charfreq         Show character histogram"
	@echo "    lists            Create lists of lstmf filenames for training and eval"
	@echo "    training         Start training"
	@echo "    traineddata      Create best and fast .traineddata files from each .checkpoint file"
	@echo "    proto-model      Build the proto model"
	@echo "    leptonica        Build leptonica"
	@echo "    tesseract        Build tesseract"
	@echo "    tesseract-langs  Download minimal stock models"
	@echo "    tesseract-langdata  Download stock unicharsets"
	@echo "    clean-box        Clean generated .box files"
	@echo "    clean-lstmf      Clean generated .lstmf files"
	@echo "    clean-output     Clean generated output files"
	@echo "    clean            Clean all generated files"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    TESSDATA           Path to the .traineddata directory with traineddata suitable for training "
	@echo "                       (for example from tesseract-ocr/tessdata_best). Default: $(TESSDATA)"
	@echo "    MODEL_NAME         Name of the model to be built. Default: $(MODEL_NAME)"
	@echo "    DATA_DIR           Data directory for output files, proto model, start model, etc. Default: $(DATA_DIR)"
	@echo "    LANGDATA_DIR       Data directory for langdata (downloaded from Tesseract langdata repo). Default: $(LANGDATA_DIR)"
	@echo "    OUTPUT_DIR         Output directory for generated files. Default: $(OUTPUT_DIR)"
	@echo "    GROUND_TRUTH_DIR   Ground truth directory. Default: $(GROUND_TRUTH_DIR)"
	@echo "    WORDLIST_FILE      Optional Wordlist file for Dictionary dawg. Default: $(WORDLIST_FILE)"
	@echo "    NUMBERS_FILE       Optional Numbers file for number patterns dawg. Default: $(NUMBERS_FILE)"
	@echo "    PUNC_FILE          Optional Punc file for Punctuation dawg. Default: $(PUNC_FILE)"
	@echo "    START_MODEL        Name of the model to continue from. Default: '$(START_MODEL)'"
	@echo "    PROTO_MODEL        Name of the proto model. Default: '$(PROTO_MODEL)'"
	@echo "    CORES              No of cores to use for compiling leptonica/tesseract. Default: $(CORES)"
	@echo "    LEPTONICA_VERSION  Leptonica version. Default: $(LEPTONICA_VERSION)"
	@echo "    TESSERACT_VERSION  Tesseract commit. Default: $(TESSERACT_VERSION)"
	@echo "    TESSDATA_REPO      Tesseract model repo to use (_fast or _best). Default: $(TESSDATA_REPO)"
	@echo "    MAX_ITERATIONS     Max iterations. Default: $(MAX_ITERATIONS)"
	@echo "    EPOCHS             Set max iterations based on the number of lines for the training. Default: none"
	@echo "    DEBUG_INTERVAL     Debug Interval. Default:  $(DEBUG_INTERVAL)"
	@echo "    LEARNING_RATE      Learning rate. Default: $(LEARNING_RATE)"
	@echo "    NET_SPEC           Network specification. Default: $(NET_SPEC)"
	@echo "    LANG_TYPE          Language Type - Indic, RTL or blank. Default: '$(LANG_TYPE)'"
	@echo "    PSM                Page segmentation mode. Default: $(PSM)"
	@echo "    RANDOM_SEED        Random seed for shuffling of the training data. Default: $(RANDOM_SEED)"
	@echo "    RATIO_TRAIN        Ratio of train / eval training data. Default: $(RATIO_TRAIN)"
	@echo "    TARGET_ERROR_RATE  Default Target Error Rate. Default: $(TARGET_ERROR_RATE)"

# END-EVAL

.PRECIOUS: $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)*_checkpoint

.PHONY: clean help leptonica lists proto-model tesseract tesseract-langs tesseract-langdata training unicharset charfreq

ALL_FILES = $(and $(wildcard $(GROUND_TRUTH_DIR)),$(shell find -L $(GROUND_TRUTH_DIR) -name '*.gt.txt'))
unexport ALL_FILES # prevent adding this to envp in recipes (which can cause E2BIG if too long; cf. make #44853)
ALL_GT = $(OUTPUT_DIR)/all-gt
ALL_LSTMF = $(OUTPUT_DIR)/all-lstmf

# Create unicharset
unicharset: $(OUTPUT_DIR)/unicharset

# Show character histogram
charfreq: $(ALL_GT)
	LC_ALL=C.UTF-8 grep -o . $< | sort | uniq -c | sort -rn

# Create lists of lstmf filenames for training and eval
lists: $(OUTPUT_DIR)/list.train $(OUTPUT_DIR)/list.eval

$(OUTPUT_DIR):
	@mkdir -p $@

$(OUTPUT_DIR)/list.eval \
$(OUTPUT_DIR)/list.train: $(ALL_LSTMF) | $(OUTPUT_DIR)
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

ifdef START_MODEL
$(DATA_DIR)/$(START_MODEL)/$(MODEL_NAME).lstm-unicharset:
	@mkdir -p $(@D)
	combine_tessdata -u $(TESSDATA)/$(START_MODEL).traineddata $(basename $@)
$(OUTPUT_DIR)/my.unicharset: $(ALL_GT) | $(OUTPUT_DIR)
	unicharset_extractor --output_unicharset "$@" --norm_mode $(NORM_MODE) "$^"
$(OUTPUT_DIR)/unicharset: $(DATA_DIR)/$(START_MODEL)/$(MODEL_NAME).lstm-unicharset $(OUTPUT_DIR)/my.unicharset
	merge_unicharsets $^ "$@"
else
$(OUTPUT_DIR)/unicharset: $(ALL_GT) | $(OUTPUT_DIR)
	unicharset_extractor --output_unicharset "$@" --norm_mode $(NORM_MODE) "$(ALL_GT)"
endif

# Start training
training: $(OUTPUT_DIR).traineddata

$(ALL_GT): $(ALL_FILES) | $(OUTPUT_DIR)
	$(if $^,,$(error found no $(GROUND_TRUTH_DIR)/*.gt.txt for $@))
	$(file >$@) $(foreach F,$^,$(file >>$@,$(file <$F)))

.PRECIOUS: %.box
%.box: %.png %.gt.txt
	PYTHONIOENCODING=utf-8 python3 $(GENERATE_BOX_SCRIPT) -i "$*.png" -t "$*.gt.txt" > "$@"

%.box: %.bin.png %.gt.txt
	PYTHONIOENCODING=utf-8 python3 $(GENERATE_BOX_SCRIPT) -i "$*.bin.png" -t "$*.gt.txt" > "$@"

%.box: %.nrm.png %.gt.txt
	PYTHONIOENCODING=utf-8 python3 $(GENERATE_BOX_SCRIPT) -i "$*.nrm.png" -t "$*.gt.txt" > "$@"

%.box: %.raw.png %.gt.txt
	PYTHONIOENCODING=utf-8 python3 $(GENERATE_BOX_SCRIPT) -i "$*.raw.png" -t "$*.gt.txt" > "$@"

%.box: %.tif %.gt.txt
	PYTHONIOENCODING=utf-8 python3 $(GENERATE_BOX_SCRIPT) -i "$*.tif" -t "$*.gt.txt" > "$@"

$(ALL_LSTMF): $(ALL_FILES:%.gt.txt=%.lstmf)
	$(if $^,,$(error found no $(GROUND_TRUTH_DIR)/*.lstmf for $@))
	@mkdir -p $(@D)
	$(file >$@) $(foreach F,$^,$(file >>$@,$F))
	python3 shuffle.py $(RANDOM_SEED) "$@"

.PRECIOUS: %.lstmf
%.lstmf: %.png %.box
	set -x; \
	tesseract "$<" $* --psm $(PSM) lstm.train

%.lstmf: %.bin.png %.box
	set -x; \
	tesseract "$<" $* --psm $(PSM) lstm.train

%.lstmf: %.nrm.png %.box
	set -x; \
	tesseract "$<" $* --psm $(PSM) lstm.train

%.lstmf: %.raw.png %.box
	set -x; \
	tesseract "$<" $* --psm $(PSM) lstm.train

%.lstmf: %.tif %.box
	set -x; \
	tesseract "$<" $* --psm $(PSM) lstm.train

CHECKPOINT_FILES := $(wildcard $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)*.checkpoint)
.PHONY: traineddata

# Create best and fast .traineddata files from each .checkpoint file
traineddata: $(OUTPUT_DIR)/tessdata_best $(OUTPUT_DIR)/tessdata_fast

traineddata: $(subst checkpoints,tessdata_best,$(patsubst %.checkpoint,%.traineddata,$(CHECKPOINT_FILES)))
traineddata: $(subst checkpoints,tessdata_fast,$(patsubst %.checkpoint,%.traineddata,$(CHECKPOINT_FILES)))
$(OUTPUT_DIR)/tessdata_best $(OUTPUT_DIR)/tessdata_fast:
	@mkdir -p $@
$(OUTPUT_DIR)/tessdata_best/%.traineddata: $(OUTPUT_DIR)/checkpoints/%.checkpoint | $(OUTPUT_DIR)/tessdata_best
	lstmtraining \
          --stop_training \
          --continue_from $< \
          --traineddata $(PROTO_MODEL) \
          --model_output $@
$(OUTPUT_DIR)/tessdata_fast/%.traineddata: $(OUTPUT_DIR)/checkpoints/%.checkpoint | $(OUTPUT_DIR)/tessdata_fast
	lstmtraining \
          --stop_training \
          --continue_from $< \
          --traineddata $(PROTO_MODEL) \
          --convert_to_int \
          --model_output $@

# Build the proto model
proto-model: $(PROTO_MODEL)

$(PROTO_MODEL): $(OUTPUT_DIR)/unicharset $(TESSERACT_LANGDATA)
	combine_lang_model \
	  --input_unicharset $(OUTPUT_DIR)/unicharset \
	  --script_dir $(LANGDATA_DIR) \
	  --numbers $(NUMBERS_FILE) \
	  --puncs $(PUNC_FILE) \
	  --words $(WORDLIST_FILE) \
	  --output_dir $(DATA_DIR) \
	  $(RECODER) \
	  --lang $(MODEL_NAME)

ifdef START_MODEL
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	@mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --debug_interval $(DEBUG_INTERVAL) \
	  --traineddata $(PROTO_MODEL) \
	  --old_traineddata $(TESSDATA)/$(START_MODEL).traineddata \
	  --continue_from $(DATA_DIR)/$(START_MODEL)/$(MODEL_NAME).lstm \
	  --learning_rate $(LEARNING_RATE) \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME) \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --max_iterations $(MAX_ITERATIONS) \
	  --target_error_rate $(TARGET_ERROR_RATE)
$(OUTPUT_DIR).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
else
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	@mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --debug_interval $(DEBUG_INTERVAL) \
	  --traineddata $(PROTO_MODEL) \
	  --learning_rate $(LEARNING_RATE) \
	  --net_spec "$(subst c###,c`head -n1 $(OUTPUT_DIR)/unicharset`,$(NET_SPEC))" \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME) \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --max_iterations $(MAX_ITERATIONS) \
	  --target_error_rate $(TARGET_ERROR_RATE)
$(OUTPUT_DIR).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
endif

TESSERACT_SCRIPTS := Arabic Armenian Bengali Bopomofo Canadian_Aboriginal Cherokee Cyrillic
TESSERACT_SCRIPTS += Devanagari Ethiopic Georgian Greek Gujarati Gurmukhi
TESSERACT_SCRIPTS += Hangul Han Hebrew Hiragana Kannada Katakana Khmer Lao Latin
TESSERACT_SCRIPTS += Malayalam Myanmar Ogham Oriya Runic Sinhala Syriac Tamil Telugu Thai

TESSERACT_LANGDATA = $(LANGDATA_DIR)/radical-stroke.txt $(TESSERACT_SCRIPTS:%=$(LANGDATA_DIR)/%.unicharset)

tesseract-langdata: $(TESSERACT_LANGDATA)

$(TESSERACT_LANGDATA):
	@mkdir -p $(@D)
	wget -O $@ 'https://github.com/tesseract-ocr/langdata_lstm/raw/main/$(@F)'

# Build leptonica
leptonica: leptonica.built

leptonica.built: leptonica-$(LEPTONICA_VERSION)
	cd $< ; \
		./configure --prefix=$(LOCAL) && \
		make -j$(CORES) install SUBDIRS=src && \
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
			make -j$(CORES) install && \
		LDFLAGS="-L$(LOCAL)/lib"\
			make -j$(CORES) training-install && \
		date > "$@"

tesseract-$(TESSERACT_VERSION):
	wget https://github.com/tesseract-ocr/tesseract/archive/$(TESSERACT_VERSION).zip
	unzip $(TESSERACT_VERSION).zip

# Download tesseract-langs
tesseract-langs: $(TESSDATA)/eng.traineddata

$(TESSDATA)/%.traineddata:
	wget -O $@ 'https://github.com/tesseract-ocr/tessdata$(TESSDATA_REPO)/raw/main/$(@F)'

# Clean generated .box files
.PHONY: clean-box
clean-box:
	find -L $(GROUND_TRUTH_DIR) -name '*.box' -delete

# Clean generated .lstmf files
.PHONY: clean-lstmf
clean-lstmf:
	find -L $(GROUND_TRUTH_DIR) -name '*.lstmf' -delete

# Clean generated output files
.PHONY: clean-output
clean-output:
	rm -rf $(OUTPUT_DIR)

# Clean all generated files
clean: clean-box clean-lstmf clean-output	
