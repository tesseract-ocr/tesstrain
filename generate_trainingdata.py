# -*- coding: utf-8 -*-
"""ULB DD/IT OCR create training data pairs"""

import argparse
import os

from lib.trainingdata import (
    TrainingData
)

DEFAULT_MIN_CHARS = 32

########
# MAIN #
########
APP_ARGUMENTS = argparse.ArgumentParser()
APP_ARGUMENTS.add_argument("-d", "--data", required=True, help="path alto|page file")
APP_ARGUMENTS.add_argument("-i", "--image", required=True, help="path image file tif|jpg")
APP_ARGUMENTS.add_argument("-o", "--output", required=False, help="path output data")
APP_ARGUMENTS.add_argument("-m", "--minchars", required=False, help="Minimum chars for a line")

ARGS = vars(APP_ARGUMENTS.parse_args())
PATH_ALTO = ARGS["data"]
PATH_SCAN = ARGS["image"]
FOLDER_OUTPUT = ARGS['output']
MIN_CHARS = ARGS['minchars']
if not MIN_CHARS:
    MIN_CHARS = DEFAULT_MIN_CHARS
else:
    MIN_CHARS = int(MIN_CHARS)

if os.path.exists(PATH_ALTO) and os.path.exists(PATH_SCAN):
    TRAINING_DATA = TrainingData(PATH_ALTO, PATH_SCAN)
    RESULT = TRAINING_DATA.create(folder_out=FOLDER_OUTPUT, min_chars=MIN_CHARS)
    print("[SUCCESS] created '{}' training data sets, please review".format(len(RESULT)))
else:
    print('[ERROR] missing ALTO "{}" or TIF "{}"!'.format(PATH_ALTO, PATH_SCAN))
