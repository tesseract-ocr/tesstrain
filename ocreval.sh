#!/bin/bash
# $1 - MODEL_NAME
# $2 - FAST_PATH_TRAINEDDATA
## Not using  -c thresholding_method=2 -c tessedit_do_invert=0

MODEL_NAME=$1
IMG_EXT=tif
FAST_PATH=data/$MODEL_NAME/tessdata_fast
FAST_PATH_TRAINEDDATA=$2
REPORTS_PATH=data/${MODEL_NAME}/reports/
EVAL_IMAGES=data/ground-truth/${MODEL_NAME}-eval/*.tif

rm -rf ${REPORTS_PATH}
mkdir -p ${REPORTS_PATH}

for model in ${FAST_PATH_TRAINEDDATA} ; do
    FAST_MODEL_NAME=$(basename $model .traineddata)
    mkdir -p ${REPORTS_PATH}/${FAST_MODEL_NAME}
    combine_tessdata -l ${FAST_PATH}/${FAST_MODEL_NAME}.traineddata
    touch ${REPORTS_PATH}/${FAST_MODEL_NAME}/OCR.txt
    touch ${REPORTS_PATH}/${FAST_MODEL_NAME}/GT.txt

    for img in ${EVAL_IMAGES}; do
        time -p tesseract \
         ${img} \
         ${REPORTS_PATH}/${FAST_MODEL_NAME}/img \
         -l ${FAST_MODEL_NAME} --tessdata-dir ${FAST_PATH} \
         -c page_separator=''
        cat ${REPORTS_PATH}/${FAST_MODEL_NAME}/img.txt | tee -a ${REPORTS_PATH}/${FAST_MODEL_NAME}/OCR.txt >/dev/null
        cat ${img%.${IMG_EXT}}.gt.txt | tee -a ${REPORTS_PATH}/${FAST_MODEL_NAME}/GT.txt >/dev/null
    done
    rm ${REPORTS_PATH}/${FAST_MODEL_NAME}/img.txt

    java -cp ~/ocreval.jar eu.digitisation.Main \
        -gt ${REPORTS_PATH}/${FAST_MODEL_NAME}/GT.txt -e UTF-8  \
        -ocr ${REPORTS_PATH}/${FAST_MODEL_NAME}/OCR.txt -e UTF-8  \
        -o ${FAST_PATH}/${FAST_MODEL_NAME}.ocrevaluation.html

     accuracy ${REPORTS_PATH}/${FAST_MODEL_NAME}/GT.txt ${REPORTS_PATH}/${FAST_MODEL_NAME}/OCR.txt \
        > ${FAST_PATH}/${FAST_MODEL_NAME}.accuracy.txt

    grep '<td>CER</td><td>' ${FAST_PATH}/*.html > ${REPORTS_PATH}/${MODEL_NAME}-CER-sorted.txt
    sed -i 's/\(.*html:\)\( *\)\(.*\)/\3 \1/g' ${REPORTS_PATH}/${MODEL_NAME}-CER-sorted.txt
    sort -V -o ${REPORTS_PATH}/${MODEL_NAME}-CER-sorted.txt ${REPORTS_PATH}/${MODEL_NAME}-CER-sorted.txt

    grep '<td>WER</td><td>' ${FAST_PATH}/*.html > ${REPORTS_PATH}/${MODEL_NAME}-WER-sorted.txt
    sed -i  's/\(.*html:\)\( *\)\(.*\)/\3 \1/g' ${REPORTS_PATH}/${MODEL_NAME}-WER-sorted.txt
    sort -V -o ${REPORTS_PATH}/${MODEL_NAME}-WER-sorted.txt ${REPORTS_PATH}/${MODEL_NAME}-WER-sorted.txt

done


