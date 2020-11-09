
# Training Type with START_MODEL - Layer or blank. Default: '$(TRAIN_TYPE)'
TRAIN_TYPE ?=

# Replace top layer of network OR plus_minus training
ifeq ($(TRAIN_TYPE),Layer)
	START_MODEL_TRAIN_STRING =--append_index 5 --net_spec '[Lfx256O1c1]'
else
	START_MODEL_TRAIN_STRING =--old_traineddata $(TESSDATA)/$(START_MODEL).traineddata
endif

FAST_FILES := $(wildcard ../data/IAST/tessdata_fast/*_[0-1].[0-9]*.traineddata)
objects = $(subst tessdata_fast,tessdata_fast,$(patsubst %.traineddata,%.dummyfile,$(FAST_FILES)))

all: $(objects)
.PHONY: all

$(objects): %.dummyfile: %.traineddata
	echo "***** $< ****"
	echo $(START_MODEL_TRAIN_STRING)
	OMP_THREAD_LIMIT=1 lstmeval  \
    --model $< \
    --eval_listfile list.zzz  2>&1  $@
