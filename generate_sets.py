# -*- coding: utf-8 -*-
"""Generate Sets of Training Data TextLine + Image Pairs"""

import argparse
import os

from sets.training_sets import (
    TrainingSets,
    DEFAULT_MIN_CHARS
)


########
# MAIN #
########
APP_ARGUMENTS = argparse.ArgumentParser()
APP_ARGUMENTS.add_argument(
    "-d",
    "--data",
    required=True,
    help="path alto|page file")
APP_ARGUMENTS.add_argument(
    "-i",
    "--image",
    required=True,
    help="path image file tif|jpg|png")
APP_ARGUMENTS.add_argument(
    "-o",
    "--output",
    required=False,
    help="path output data")
APP_ARGUMENTS.add_argument(
    "-m",
    "--minchars",
    required=False,
    help="Minimum chars for a line")
APP_ARGUMENTS.add_argument(
    "-s",
    "--summary",
    required=False,
    help="Summarize all lines")
APP_ARGUMENTS.add_argument(
    "-r",
    "--revert",
    required=False,
    help="Revert word reading order")

ARGS = vars(APP_ARGUMENTS.parse_args())
PATH_OCR = ARGS["data"]
PATH_IMG = ARGS["image"]
FOLDER_OUTPUT = ARGS['output']
MIN_CHARS = ARGS['minchars']
SUMMARY = ARGS['summary']
REVERT = ARGS['revert']
if not MIN_CHARS:
    MIN_CHARS = DEFAULT_MIN_CHARS
else:
    MIN_CHARS = int(MIN_CHARS)
if not SUMMARY:
    SUMMARY = False
if not REVERT:
    REVERT = False

if os.path.exists(PATH_OCR) and os.path.exists(PATH_IMG):
    TRAINING_DATA = TrainingSets(PATH_OCR, PATH_IMG)
    RESULT = TRAINING_DATA.create(
        folder_out=FOLDER_OUTPUT,
        min_chars=MIN_CHARS,
        summary=SUMMARY,
        revert=REVERT)
    print(
        "[SUCCESS] created '{}' training data sets, please review".format(
            len(RESULT)))
else:
    print(
        "[ERROR] missing OCR '{}' or Image Data '{}'!".format(
            PATH_OCR,
            PATH_IMG))
