SHELL := /bin/bash

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    data/unicharset  Create unicharset"
	@echo "    lists            Create lists of lstmf files for training and eval"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    TRAIN        Train directory"
	@echo "    RATIO_TRAIN  Ratio of train / eval training data"
	@echo "    BOX_FILES    Box files"
	@echo "    LSTMF_FILES  lstmf files"

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
data/unicharset: $(ALL_BOXES)
	unicharset_extractor --output_unicharset "$@" --norm_mode 1 "$(ALL_BOXES)"
	rm "$(ALL_BOXES)"

$(ALL_BOXES): $(BOX_FILES)

$(TRAIN)/%.box: $(TRAIN)/%.tif $(TRAIN)/%.gt.txt
	python generate_line_box.py -i "$(TRAIN)/$*.tif" -t "$(TRAIN)/$*.gt.txt" > "$@"
	cat "$@" >> $(ALL_BOXES)

$(TRAIN)/%.lstmf: $(TRAIN)/%.box
	tesseract $(TRAIN)/$*.tif $(TRAIN)/$* lstm.train
	echo "$@" >> $(ALL_LSTMF)

$(ALL_LSTMF): $(LSTMF_FILES)
	cat "$@" | sort -R > /tmp/sortfoobla
	mv /tmp/sortfoobla "$@"

# Create lists of lstmf files for training and eval
lists: $(ALL_LSTMF)
	no=`cat $(ALL_LSTMF) | wc -l` \
	   no_train=`echo "$$no * $(RATIO_TRAIN) / 1" | bc` \
	   no_eval=`echo "$$no * $$(( 1 - $(RATIO_TRAIN) )) / 1" | bc`; \
	   head -n "$$no_train" $(ALL_LSTMF) > data/list.train; \
	   head -n "$$no_eval" $(ALL_LSTMF) > data/list.eval;
