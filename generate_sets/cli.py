# -*- coding: utf-8 -*-
"""Generate Sets of Training Data TextLine + Image Pairs"""

import argparse
import os

from . import (
    TrainingSets,
    DEFAULT_OUTDIR_PREFIX,
    DEFAULT_MIN_CHARS,
    DEFAULT_USE_SUMMARY,
    DEFAULT_USE_REORDER,
    SUMMARY_SUFFIX
)


########
# MAIN #
########
PARSER = argparse.ArgumentParser(description="generate pairs of textlines and image frames from existing OCR and image data")
PARSER.add_argument(
    "data",
    type=str,
    help="path to local alto|page file corresponding to image")
PARSER.add_argument(
    "-i",
    "--image",
    required=False,
    help="path to local image file tif|jpg|png corresponding to ocr. (default: read from OCR-Data)")
PARSER.add_argument(
    "-o",
    "--output",
    required=False,
    help="optional: output directory, re-created if already exists. (default: <script-dir>/<{}-ocr-name>)".format(DEFAULT_OUTDIR_PREFIX))
PARSER.add_argument(
    "-m",
    "--minchars",
    required=False,
    type=int,
    default=int(DEFAULT_MIN_CHARS),
    help="optional: minimum printable chars required for a line to be included into set (default: {})".format(DEFAULT_MIN_CHARS))
PARSER.add_argument(
    "-s",
    "--summary",
    required=False,
    action='store_true',
    default=DEFAULT_USE_SUMMARY,
    help="optional: print all lines in additional file (default: {}, pattern: <default-output-dir>{})".format(DEFAULT_USE_SUMMARY, SUMMARY_SUFFIX))
PARSER.add_argument(
    "-r",
    "--reorder",
    required=False,
    action='store_true',
    default=DEFAULT_USE_REORDER,
    help="optional: re-order word tokens from right-to-left (default: {})".format(DEFAULT_USE_REORDER))

ARGS = PARSER.parse_args()
PATH_OCR = ARGS.data
PATH_IMG = ARGS.image
FOLDER_OUTPUT = ARGS.output
MIN_CHARS = ARGS.minchars
SUMMARY = ARGS.summary
REORDER = ARGS.reorder

if os.path.exists(PATH_OCR):
    print("[INFO   ] generate trainingsets of '{}' with '{}' (min: {}, sum: {}, reorder: {})".format(
        PATH_OCR, PATH_IMG, MIN_CHARS, SUMMARY, REORDER))
    TRAINING_DATA = TrainingSets(PATH_OCR, PATH_IMG)
    RESULT = TRAINING_DATA.create(
        folder_out=FOLDER_OUTPUT,
        min_chars=MIN_CHARS,
        summary=SUMMARY,
        reorder=REORDER)
    print(
        "[SUCCESS] created '{}' training data sets in '{}', please review".format(
            len(RESULT), TRAINING_DATA.path_out))
else:
    print(
        "[ERROR  ] missing OCR '{}' or Image Data '{}'!".format(
            PATH_OCR,
            PATH_IMG))
