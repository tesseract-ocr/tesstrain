export PYTHONIOENCODING=utf8

## Make sure that sort always uses the same sort order.
LC_ALL := C

SHELL := /bin/bash
LOCAL := $(PWD)/usr
PATH := $(LOCAL)/bin:$(PATH)
TESSDATA =  $(LOCAL)/share/tessdata
TESSDATA_BEST = ~/tessdata_best
SCRIPT_DIR = data

# Name of the model to be built. Default: $(MODEL_NAME)
MODEL_NAME = foo

# Output directory for generated files. Default: $(OUTPUT_DIR)
OUTPUT_DIR = data/$(MODEL_NAME)

# Ground truth directory. Default: $(GROUND_TRUTH_DIR)
GROUND_TRUTH_DIR := data/ground-truth

# Directory with font files for generating box-tiff pairs using text2image. Default: $(FONTS_DIR)
FONTS_DIR = /usr/share/fonts

# List of font names for generating box-tiff pairs using text2image. Default: $(FONTS_LIST)
FONTS_LIST =

#Training text for generating box-tiff pairs using text2image. Default: $(TRAINING_TEXT)
TRAINING_TEXT =

# Wordlist file for Dictionary dawg. Default: $(WORDLIST_FILE)
WORDLIST_FILE = $(GROUND_TRUTH_DIR)/$(MODEL_NAME).wordlist

# Numbers file for number patterns dawg. Default: $(NUMBERS_FILE)
NUMBERS_FILE = $(GROUND_TRUTH_DIR)/$(MODEL_NAME).numbers

# Punc file for Punctuation dawg. Default: $(PUNC_FILE)
PUNC_FILE = $(GROUND_TRUTH_DIR)/$(MODEL_NAME).punc

# Name of the model to continue from. Default: '$(START_MODEL)'
START_MODEL =

LAST_CHECKPOINT = $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE)_checkpoint

# Name of the proto model (starter traineddata). Default: '$(PROTO_MODEL)'
PROTO_MODEL = $(OUTPUT_DIR)/$(MODEL_NAME).traineddata

# No of cores to use for compiling leptonica/tesseract. Default: $(CORES)
CORES = 4

# Leptonica version. Default: $(LEPTONICA_VERSION)
LEPTONICA_VERSION := 1.78.0

# Tesseract commit. Default: $(TESSERACT_VERSION)
TESSERACT_VERSION := 4.1.0

# Tesseract model repo to use. Default: $(TESSDATA_REPO)
TESSDATA_REPO = _best

# Max iterations. Default: $(MAX_ITERATIONS)
MAX_ITERATIONS := 10000

# Network specification for training from scratch. Default: $(NET_SPEC)
NET_SPEC := [1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx192 O1c1]

# Training Build Type - Impact, Plus, Layer or Scratch. Default: '$(BUILD_TYPE)'
BUILD_TYPE = Scratch

# Language Type - Indic, RTL or blank. Default: '$(LANG_TYPE)'
LANG_TYPE ?=

# Normalization mode - 2, 1 - for unicharset_extractor and Pass through Recoder for combine_lang_model
ifeq ($(LANG_TYPE),Indic)
    NORM_MODE =2
    RECODER=--pass_through_recoder
else
ifeq ($(LANG_TYPE),RTL)
    NORM_MODE =2
    RECODER=--pass_through_recoder --lang_is_rtl
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
RATIO_TRAIN := 0.99

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    unicharset       Create unicharset"
	@echo "    lists            Create lists of lstmf filenames for training and eval"
	@echo "    training         Start training"
	@echo "    proto-model      Build the proto model"
	@echo "    leptonica        Build leptonica"
	@echo "    tesseract        Build tesseract"
	@echo "    tesseract-langs  Download tesseract-langs"
	@echo "    clean            Clean all generated files"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    MODEL_NAME         Name of the model to be built. Default: $(MODEL_NAME)"
	@echo "    OUTPUT_DIR         Output directory for generated files. Default: $(OUTPUT_DIR)"
	@echo "    START_MODEL        Name of the model to continue from. Default: '$(START_MODEL)'"
	@echo "    PROTO_MODEL        Name of the proto model. Default: '$(PROTO_MODEL)'"
	@echo "    CORES              No of cores to use for compiling leptonica/tesseract. Default: $(CORES)"
	@echo "    LEPTONICA_VERSION  Leptonica version. Default: $(LEPTONICA_VERSION)"
	@echo "    TESSERACT_VERSION  Tesseract commit. Default: $(TESSERACT_VERSION)"
	@echo "    TESSDATA_REPO      Tesseract model repo to use. Default: $(TESSDATA_REPO)"
	@echo "    GROUND_TRUTH_DIR   Ground truth directory. Default: $(GROUND_TRUTH_DIR)"
	@echo "    MAX_ITERATIONS     Max iterations. Default: $(MAX_ITERATIONS)"
	@echo "    NET_SPEC           Network specification for training from scratch. Default: $(NET_SPEC)"
	@echo "    BUILD_TYPE      Training Type - Impact, Plus, Layer or Scratch. Default: '$(BUILD_TYPE)'"
	@echo "    LANG_TYPE          Language Type - Indic, RTL or blank. Default: '$(LANG_TYPE)'"
	@echo "    NORM_MODE          Normalization Mode - see src/training/language_specific.sh for details. Default: $(NORM_MODE)"
	@echo "    PSM                Page segmentation mode. Default: $(PSM)"
	@echo "    RANDOM_SEED        Random seed for shuffling of the training data. Default: $(RANDOM_SEED)"
	@echo "    RATIO_TRAIN        Ratio of train / eval training data. Default: $(RATIO_TRAIN)"

# END-EVAL

.PHONY: clean help leptonica lists proto-model tesseract tesseract-langs training unicharset

.PRECIOUS: $(GROUND_TRUTH_DIR)/%.box $(GROUND_TRUTH_DIR)/%.lstmf

ALL_GT = $(OUTPUT_DIR)/all-gt
ALL_LSTMF = $(OUTPUT_DIR)/all-lstmf

ifdef TRAINING_TEXT
$(ALL_GT): $(FONTS_LIST) $(TRAINING_TEXT)
	while read -r fontname; do \
		LINENUM=0; \
		while read -r trainline; do \
			((LINENUM = LINENUM + 1)); \
			echo "$$trainline" >tmp.txt; \
			OMP_THREAD_LIMIT=1   text2image  --strip_unrenderable_words --xsize=2500 --ysize=152  --leading=32 --margin=12  --char_spacing=0.0 --exposure=0  --max_pages=0  --fonts_dir=$(FONTS_DIR) --font="$$fontname" --text=tmp.txt  --outputbase="$(GROUND_TRUTH_DIR)/$${fontname// /_}-$$LINENUM.exp0"; \
		done < $(TRAINING_TEXT); \
	done < $(FONTS_LIST); \
	mkdir -p $(OUTPUT_DIR); \
	cp "$(TRAINING_TEXT)"  "$(ALL_GT)"
else
$(ALL_GT): $(patsubst $(GROUND_TRUTH_DIR)/%.tif,$(GROUND_TRUTH_DIR)/%.gt.txt,$(shell find $(GROUND_TRUTH_DIR) -name '*.tif'))
	mkdir -p $(OUTPUT_DIR)
	find $(GROUND_TRUTH_DIR) -name '*.gt.txt' | xargs -I{} sh -c "cat {}; echo ''" | sort -u > "$@"

$(GROUND_TRUTH_DIR)/%.box: $(GROUND_TRUTH_DIR)/%.tif $(GROUND_TRUTH_DIR)/%.gt.txt
	python3 generate_wordstr_box.py  -i "$(GROUND_TRUTH_DIR)/$*.tif" -t "$(GROUND_TRUTH_DIR)/$*.gt.txt" > "$@"
endif


# Create unicharset
unicharset: $(OUTPUT_DIR)/unicharset

ifeq ($(BUILD_TYPE),Plus)
$(OUTPUT_DIR)/unicharset:  $(ALL_GT) 
	mkdir -p $(OUTPUT_DIR)
	unicharset_extractor --output_unicharset "$(GROUND_TRUTH_DIR)/my.unicharset" --norm_mode $(NORM_MODE) "$(ALL_GT)"
	merge_unicharsets data/$(START_MODEL)/$(MODEL_NAME).lstm-unicharset $(GROUND_TRUTH_DIR)/my.unicharset  "$@"
else
$(OUTPUT_DIR)/unicharset:  $(ALL_GT) 
	mkdir -p $(OUTPUT_DIR)
	unicharset_extractor --output_unicharset "$@" --norm_mode $(NORM_MODE) "$(ALL_GT)"
endif

# Create lists of lstmf filenames for training and eval
lists: $(OUTPUT_DIR)/list.train $(OUTPUT_DIR)/list.eval

$(OUTPUT_DIR)/list.eval \
$(OUTPUT_DIR)/list.train:  $(ALL_LSTMF)
	mkdir -p $(OUTPUT_DIR)
	total=$$(wc -l < $(ALL_LSTMF)); \
	  train=$$(echo "$$total * $(RATIO_TRAIN) / 1" | bc); \
	  test "$$train" = "0" && \
	    echo "Error: missing ground truth for training" && exit 1; \
	  eval=$$(echo "$$total - $$train" | bc); \
	  test "$$eval" = "0" && \
	    echo "Error: missing ground truth for evaluation" && exit 1; \
	  head -n "$$train" $(ALL_LSTMF) > "$(OUTPUT_DIR)/list.train"; \
	  tail -n "$$eval" $(ALL_LSTMF) > "$(OUTPUT_DIR)/list.eval"

# Start training
training:  startmodelfiles  $(OUTPUT_DIR)$(BUILD_TYPE).traineddata

ifdef START_MODEL
startmodelfiles: $(TESSDATA_BEST)/$(START_MODEL).traineddata data/$(START_MODEL)/$(MODEL_NAME).lstm-unicharset data/$(START_MODEL)/$(MODEL_NAME).lstm

$(TESSDATA_BEST)/$(START_MODEL).traineddata:
	cd $(TESSDATA_BEST) && wget https://github.com/tesseract-ocr/tessdata$(TESSDATA_REPO)/raw/master/$(notdir $@)

data/$(START_MODEL)/$(MODEL_NAME).lstm-unicharset:
	mkdir -p data/$(START_MODEL)
	combine_tessdata -e $(TESSDATA_BEST)/$(START_MODEL).traineddata  "$@"

data/$(START_MODEL)/$(MODEL_NAME).lstm:
	mkdir -p data/$(START_MODEL)
	combine_tessdata -e $(TESSDATA_BEST)/$(START_MODEL).traineddata  "$@"
else
startmodelfiles:
	echo "No START_MODEL"
endif

lstmf: $(GROUND_TRUTH_DIR)/%.lstmf $(ALL_LSTMF)
$(ALL_LSTMF): $(patsubst %.tif,%.lstmf,$(shell find $(GROUND_TRUTH_DIR) -name '*.tif'))
	mkdir -p $(OUTPUT_DIR)
	find $(GROUND_TRUTH_DIR) -name '*.lstmf' | python3 shuffle.py $(RANDOM_SEED) > "$@"

%.lstmf: %.box
	tesseract $*.tif $* --psm $(PSM) --dpi 300 lstm.train

# Build the proto model
proto-model: $(PROTO_MODEL)

$(PROTO_MODEL): $(OUTPUT_DIR)/unicharset data/radical-stroke.txt
	combine_lang_model \
	  --input_unicharset $(OUTPUT_DIR)/unicharset \
	  --script_dir $(SCRIPT_DIR) \
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
	  --debug_interval 0 \
	  --traineddata $(TESSDATA_BEST)/$(START_MODEL).traineddata \
	  --continue_from data/$(START_MODEL)/$(MODEL_NAME).lstm \
	  --model_output $(OUTPUT_DIR)/checkpoints/$(MODEL_NAME)$(BUILD_TYPE) \
	  --train_listfile $(OUTPUT_DIR)/list.train \
	  --max_iterations $(MAX_ITERATIONS)
	lstmeval \
	  --traineddata $(TESSDATA_BEST)/$(START_MODEL).traineddata \
	  --model $(LAST_CHECKPOINT) \
	  --eval_listfile $(OUTPUT_DIR)/list.eval \
	  --verbosity 0
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--convert_to_int \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(TESSDATA_BEST)/$(START_MODEL).traineddata \
	--model_output $@
endif
ifeq ($(BUILD_TYPE),Plus)
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --old_traineddata $(TESSDATA_BEST)/$(START_MODEL).traineddata \
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
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--convert_to_int \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
endif
ifeq ($(BUILD_TYPE),Layer)
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --append_index 5 --net_spec '[Lfx192 O1c1]' \
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
$(OUTPUT_DIR)$(BUILD_TYPE).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--convert_to_int \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@
endif
else
ifeq ($(BUILD_TYPE),Scratch)
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	mkdir -p $(OUTPUT_DIR)/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --net_spec "$(subst c1,c`head -n1 $(OUTPUT_DIR)/unicharset`,$(NET_SPEC))" \
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
	--convert_to_int \
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
		LEPTONICA_CFLAGS="-I$(LOCAL)/include/leptonica" \
			./configure --prefix=$(LOCAL) && \
		LDFLAGS="-L$(LOCAL)/lib"\
			make -j$(CORES) install training-install && \
		date > "$@"

tesseract-$(TESSERACT_VERSION):
	wget https://github.com/tesseract-ocr/tesseract/archive/$(TESSERACT_VERSION).zip
	unzip $(TESSERACT_VERSION).zip

# Download tesseract-langs
tesseract-langs: $(TESSDATA_BEST)/eng.traineddata

$(TESSDATA_BEST)/eng.traineddata:
	cd $(TESSDATA_BEST) && wget https://github.com/tesseract-ocr/tessdata$(TESSDATA_REPO)/raw/master/$(notdir $@)

# Clean all generated files
cleanbox:
	find $(GROUND_TRUTH_DIR) -name '*.box' -delete
cleanlstmf:
	find $(GROUND_TRUTH_DIR) -name '*.lstmf' -delete
clean:
	rm -rf $(OUTPUT_DIR)

