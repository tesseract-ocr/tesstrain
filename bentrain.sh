make -f Makefile-font2model MODEL_NAME=bennew clean-groundtruth clean-output clean-log

make -f Makefile-font2model \
MODEL_NAME=bennew \
START_MODEL=ben \
TESSDATA=$HOME/tessdata_best \
TESSTRAIN_TEXT=$HOME/langdata_lstm/ben/ben.training_text \
TESSTRAIN_FONT=Kalpurush \
TESSTRAIN_SCRIPT=Bengali \
TESSTRAIN_FONTS_DIR=$HOME/.fonts/ben \
TESSTRAIN_MAX_LINES=10000 \
EPOCHS=10  DEBUG_INTERVAL=-1 \
training
