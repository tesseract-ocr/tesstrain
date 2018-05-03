export

SHELL := /bin/bash
LOCAL := $(PWD)/usr
PATH := $(LOCAL)/bin:$(PATH)
TESSDATA =  $(LOCAL)/share/tessdata 
LANGDATA = $(PWD)/langdata-$(LANGDATA_VERSION)

# No of cores to use
CORES = 4

# Leptonica version. Default: $(LEPTONICA_VERSION)
LEPTONICA_VERSION := 1.75.3

# Tesseract commit. Default: $(TESSERACT_VERSION)
TESSERACT_VERSION := 9ae97508aed1e5508458f1181b08501f984bf4e2

# Tesseract langdata version. Default: $(LANGDATA_VERSION)
LANGDATA_VERSION := master

# Tesseract model repo to use. Default: $(TESSDATA_REPO)
TESSDATA_REPO = _fast

# Name of the model to be built
MODEL_NAME = foo

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
	@echo "    langdata         Download langdata"
	@echo "    clean            Clean all generated files"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    CORES              No of cores to use"
	@echo "    LEPTONICA_VERSION  Leptonica version. Default: $(LEPTONICA_VERSION)"
	@echo "    TESSERACT_VERSION  Tesseract commit. Default: $(TESSERACT_VERSION)"
	@echo "    LANGDATA_VERSION   Tesseract langdata version. Default: $(LANGDATA_VERSION)"
	@echo "    TESSDATA_REPO      Tesseract model repo to use. Default: $(TESSDATA_REPO)"
	@echo "    MODEL_NAME         Name of the model to be built"
	@echo "    TRAIN              Train directory"
	@echo "    RATIO_TRAIN        Ratio of train / eval training data"
	@echo "    BOX_FILES          Box files"
	@echo "    LSTMF_FILES        lstmf files"

# END-EVAL

# Train directory
TRAIN := data/train

# Ratio of train / eval training data
RATIO_TRAIN := 0.9

# Box files
BOX_FILES = $(shell find data/train -name '*.tif' |sed 's,\.tif,.box,')

# lstmf files
LSTMF_FILES = $(shell find data/train -name '*.tif' |sed 's,\.tif,.lstmf,')

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
	   tail -n "+$$no" $(ALL_LSTMF) > "$@"

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

# Build the proto model
proto-model: data/$(MODEL_NAME)/$(MODEL_NAME).traineddata

data/$(MODEL_NAME)/$(MODEL_NAME).traineddata: $(LANGDATA) data/unicharset
	combine_lang_model \
	  --input_unicharset data/unicharset \
	  --script_dir $(LANGDATA) \
	  --output_dir data/ \
	  --lang $(MODEL_NAME)

data/checkpoints/$(MODEL_NAME)_checkpoint: unicharset lists proto-model
	mkdir -p data/checkpoints
	which lstmtraining
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

# Download langdata
langdata: $(LANGDATA)

$(LANGDATA):
	wget 'https://github.com/tesseract-ocr/langdata/archive/$(LANGDATA_VERSION).zip'
	unzip $(LANGDATA_VERSION).zip

$(TESSDATA)/eng.traineddata:
	cd $(TESSDATA) && wget https://github.com/tesseract-ocr/tessdata$(TESSDATA_REPO)/raw/master/$(notdir $@)

# Clean all generated files
clean:
	rm -rf data/train/*.box
	rm -rf data/train/*.lstmf
	rm -rf data/all-*
	rm -rf data/list.*
	rm -rf data/$(MODEL_NAME)
	rm -rf data/unicharset
	rm -rf data/checkpoints
