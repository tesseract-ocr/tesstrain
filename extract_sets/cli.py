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
    DEFAULT_INTRUSION_RATIO,
    DEFAULT_ROTATION_THRESH,
    DEFAULT_SANITIZE,
    DEFAULT_BINARIZE,
    DEFAULT_PADDING,
    SUMMARY_SUFFIX
)


########
# MAIN #
########
def main():
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
    PARSER.add_argument(
        "--binarize",
        required=False,
        action='store_true',
        default=DEFAULT_BINARIZE,
        help="optional: binarize textline images (default: {})".format(DEFAULT_BINARIZE))
    PARSER.add_argument(
        "--sanitize",
        required=False,
        type=bool,
        default=DEFAULT_SANITIZE,
        help="optional: sanitize textline images (default: {})".format(DEFAULT_SANITIZE))
    PARSER.add_argument('--no-sanitize', dest='sanitize', action='store_false')
    PARSER.add_argument(
        "--intrusion-ratio",
        required=False,
        default=DEFAULT_INTRUSION_RATIO,
        help="optional: alter threshold for top and bottom ratios for intrusion detection for sanitizing (default: {})".format(DEFAULT_INTRUSION_RATIO))
    PARSER.add_argument(
        "--rotation-threshold",
        required=False,
        type=float,
        default=DEFAULT_ROTATION_THRESH,
        help="optional: alter threshold for rotation of textline image (default: {})".format(DEFAULT_ROTATION_THRESH))
    PARSER.add_argument(
        "-p",
        "--padding",
        required=False,
        type=int,
        default=DEFAULT_PADDING,
        help="optional: additional padding for existing textline image (default: {})".format(DEFAULT_PADDING))

    ARGS = PARSER.parse_args()
    PATH_OCR = ARGS.data
    PATH_IMG = ARGS.image
    FOLDER_OUTPUT = ARGS.output
    MIN_CHARS = ARGS.minchars
    SUMMARY = ARGS.summary
    REORDER = ARGS.reorder
    BINARIZE = ARGS.binarize
    SANITIZE = ARGS.sanitize
    INTR_RATIO = ARGS.intrusion_ratio
    if isinstance(INTR_RATIO, str) and',' in INTR_RATIO:
        INTR_RATIO = [float(n) for n in INTR_RATIO.split(',')]
    else:
        INTR_RATIO = float(INTR_RATIO)
    ROTA_THRESH = ARGS.rotation_threshold
    PADDING = ARGS.padding

    if os.path.exists(PATH_OCR):
        print("[INFO ] generate trainingsets from '{}'".format(PATH_OCR))
        print("[DEBUG] args: {}".format(ARGS))
        TRAINING_DATA = TrainingSets(PATH_OCR, PATH_IMG)
        RESULT = TRAINING_DATA.create(
            folder_out=FOLDER_OUTPUT,
            min_chars=MIN_CHARS,
            summary=SUMMARY,
            reorder=REORDER,
            intrusion_ratio=INTR_RATIO, rotation_threshold=ROTA_THRESH,
            binarize=BINARIZE, sanitize=SANITIZE, padding=PADDING)
        print(
            "[SUCCESS] created '{}' training data sets from '{}' in '{}', please review".format(
                len(RESULT), PATH_OCR, TRAINING_DATA.path_out))
    else:
        print(
            "[ERROR  ] missing OCR '{}' or Image Data '{}'!".format(
                PATH_OCR,
                PATH_IMG))
