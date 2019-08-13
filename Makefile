export

SHELL := /bin/bash
LOCAL := $(PWD)/usr
PATH := $(LOCAL)/bin:$(PATH)
TESSDATA =  $(LOCAL)/share/tessdata

# Name of the model to be built. Default: $(MODEL_NAME)
MODEL_NAME = foo

# Name of the model to continue from. Default: '$(START_MODEL)'
START_MODEL = 

LAST_CHECKPOINT = data/checkpoints/$(MODEL_NAME)_checkpoint

# Name of the proto model. Default: '$(PROTO_MODEL)'
PROTO_MODEL = data/$(MODEL_NAME)/$(MODEL_NAME).traineddata

# No of cores to use for compiling leptonica/tesseract. Default: $(CORES)
CORES = 4

# Leptonica version. Default: $(LEPTONICA_VERSION)
LEPTONICA_VERSION := 1.75.3

# Tesseract commit. Default: $(TESSERACT_VERSION)
TESSERACT_VERSION := fd492062d08a2f55001a639f2015b8524c7e9ad4

# Tesseract model repo to use. Default: $(TESSDATA_REPO)
TESSDATA_REPO = _best

# Ground truth directory. Default: $(GROUND_TRUTH_DIR)
GROUND_TRUTH_DIR := data/ground-truth

# Normalization Mode - see src/training/language_specific.sh for details. Default: $(NORM_MODE)
NORM_MODE = 2

# Page segmentation mode. Default: $(PSM)
PSM = 6

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
	@echo "    GROUND_TRUTH_DIR   Ground truth directory. Default: $(GROUND_TRUTH_DIR)"
	@echo "    NORM_MODE          Normalization Mode - see src/training/language_specific.sh for details. Default: $(NORM_MODE)"
	@echo "    PSM                Page segmentation mode. Default: $(PSM)"
	@echo "    RATIO_TRAIN        Ratio of train / eval training data. Default: $(RATIO_TRAIN)"

# END-EVAL

ALL_BOXES = data/all-boxes
ALL_LSTMF = data/all-lstmf

# Create unicharset
unicharset: data/unicharset

# Create lists of lstmf filenames for training and eval
lists: $(ALL_LSTMF) data/list.train data/list.eval

data/list.train: $(ALL_LSTMF)
	total=`cat $(ALL_LSTMF) | wc -l` \
	   no=`echo "$$total * $(RATIO_TRAIN) / 1" | bc`; \
	   head -n "$$no" $(ALL_LSTMF) > "$@"

data/list.eval: $(ALL_LSTMF)
	total=`cat $(ALL_LSTMF) | wc -l` \
	   no=`echo "($$total - $$total * $(RATIO_TRAIN)) / 1" | bc`; \
	   tail -n "$$no" $(ALL_LSTMF) > "$@"

# Start training
training: data/$(MODEL_NAME).traineddata

ifdef START_MODEL
data/unicharset: $(ALL_BOXES)
	mkdir -p data/$(START_MODEL)
	combine_tessdata -u $(TESSDATA)/$(START_MODEL).traineddata  data/$(START_MODEL)/$(START_MODEL)
	unicharset_extractor --output_unicharset "$(GROUND_TRUTH_DIR)/my.unicharset" --norm_mode $(NORM_MODE) "$(ALL_BOXES)"
	merge_unicharsets data/$(START_MODEL)/$(START_MODEL).lstm-unicharset $(GROUND_TRUTH_DIR)/my.unicharset  "$@"
else
data/unicharset: $(ALL_BOXES)
	unicharset_extractor --output_unicharset "$@" --norm_mode 1 "$(ALL_BOXES)"
endif

$(ALL_BOXES): $(sort $(patsubst %.tif,%.box,$(wildcard $(GROUND_TRUTH_DIR)/*.tif)))
	find $(GROUND_TRUTH_DIR) -name '*.box' | xargs cat > "$@"

$(GROUND_TRUTH_DIR)/%.box: $(GROUND_TRUTH_DIR)/%.tif $(GROUND_TRUTH_DIR)/%.gt.txt
	python generate_line_box.py -i "$(GROUND_TRUTH_DIR)/$*.tif" -t "$(GROUND_TRUTH_DIR)/$*.gt.txt" > "$@"

$(ALL_LSTMF): $(sort $(patsubst %.tif,%.lstmf,$(wildcard $(GROUND_TRUTH_DIR)/*.tif)))
	find $(GROUND_TRUTH_DIR) -name '*.lstmf' | sort -R -o "$@"

$(GROUND_TRUTH_DIR)/%.lstmf: $(GROUND_TRUTH_DIR)/%.box
	tesseract $(GROUND_TRUTH_DIR)/$*.tif $(GROUND_TRUTH_DIR)/$* --psm $(PSM) lstm.train

# Build the proto model
proto-model: $(PROTO_MODEL)

$(PROTO_MODEL): data/unicharset data/radical-stroke.txt
	combine_lang_model \
	  --input_unicharset data/unicharset \
	  --script_dir data/ \
	  --output_dir data/ \
	  --lang $(MODEL_NAME)

ifdef START_MODEL
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	mkdir -p data/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
          --old_traineddata $(TESSDATA)/$(START_MODEL).traineddata \
	  --continue_from data/$(START_MODEL)/$(START_MODEL).lstm \
	  --net_spec "[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c`head -n1 data/unicharset`]" \
	  --model_output data/checkpoints/$(MODEL_NAME) \
	  --learning_rate 20e-4 \
	  --train_listfile data/list.train \
	  --eval_listfile data/list.eval \
	  --max_iterations 10000
else
$(LAST_CHECKPOINT): unicharset lists $(PROTO_MODEL)
	mkdir -p data/checkpoints
	lstmtraining \
	  --traineddata $(PROTO_MODEL) \
	  --net_spec "[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c`head -n1 data/unicharset`]" \
	  --model_output data/checkpoints/$(MODEL_NAME) \
	  --learning_rate 20e-4 \
	  --train_listfile data/list.train \
	  --eval_listfile data/list.eval \
	  --max_iterations 10000
endif

data/$(MODEL_NAME).traineddata: $(LAST_CHECKPOINT)
	lstmtraining \
	--stop_training \
	--continue_from $(LAST_CHECKPOINT) \
	--traineddata $(PROTO_MODEL) \
	--model_output $@

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
			make -j$(CORES) && \
		make install && \
		make -j$(CORES) training-install && \
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
	rm -rf data/all-*
	rm -rf data/list.*
	rm -rf data/$(MODEL_NAME)
	rm -rf data/unicharset
	rm -rf data/checkpoints
