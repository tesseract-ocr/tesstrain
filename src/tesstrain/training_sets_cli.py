# -*- coding: utf-8 -*-
"""Generate Sets of Training Data TextLine + Image Pairs"""

import argparse
import os

from tesstrain.training_sets import (
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
        "--prefix-output",
        required=False,
        help=f"optional: output directory, re-created if already exists. (default: <script-dir>/<{DEFAULT_OUTDIR_PREFIX}>)")
    PARSER.add_argument(
        "-m",
        "--minchars",
        required=False,
        type=int,
        default=int(DEFAULT_MIN_CHARS),
        help=f"optional: minimum printable chars required for a line to be included into set (default: {DEFAULT_MIN_CHARS})")
    PARSER.add_argument(
        "-s",
        "--summary",
        required=False,
        action='store_true',
        default=DEFAULT_USE_SUMMARY,
        help=f"optional: print all lines in additional file (default: {DEFAULT_USE_SUMMARY}, pattern: <default-output-dir>{SUMMARY_SUFFIX})")
    PARSER.add_argument(
        "-r",
        "--reorder",
        required=False,
        action='store_true',
        default=DEFAULT_USE_REORDER,
        help=f"optional: re-order word tokens from right-to-left (default: {DEFAULT_USE_REORDER})")
    PARSER.add_argument(
        "--binarize",
        required=False,
        action='store_true',
        default=DEFAULT_BINARIZE,
        help=f"optional: binarize textline images (default: {DEFAULT_BINARIZE})")
    PARSER.add_argument(
        "--sanitize",
        required=False,
        type=bool,
        default=DEFAULT_SANITIZE,
        help=f"optional: sanitize textline images (default: {DEFAULT_SANITIZE})")
    PARSER.add_argument('--no-sanitize', dest='sanitize', action='store_false')
    PARSER.add_argument(
        "--intrusion-ratio",
        required=False,
        default=DEFAULT_INTRUSION_RATIO,
        help=f"optional: alter threshold for top and bottom ratios for intrusion detection for sanitizing (default: {DEFAULT_INTRUSION_RATIO})")
    PARSER.add_argument(
        "--rotation-threshold",
        required=False,
        type=float,
        default=DEFAULT_ROTATION_THRESH,
        help=f"optional: alter threshold for rotation of textline image (default: {DEFAULT_ROTATION_THRESH})")
    PARSER.add_argument(
        "-p",
        "--padding",
        required=False,
        type=int,
        default=DEFAULT_PADDING,
        help=f"optional: additional padding for existing textline image (default: {DEFAULT_PADDING})")

    ARGS = PARSER.parse_args()
    PATH_OCR = ARGS.data
    PATH_IMG = ARGS.image
    OUTPUT_PREFIX = ARGS.prefix_output
    MIN_CHARS = ARGS.minchars
    SUMMARY = ARGS.summary
    REORDER = ARGS.reorder
    BINARIZE = ARGS.binarize
    SANITIZE = ARGS.sanitize
    INTR_RATIO = ARGS.intrusion_ratio
    if isinstance(INTR_RATIO, str) and ',' in INTR_RATIO:
        INTR_RATIO = [float(n) for n in INTR_RATIO.split(',')]
    else:
        INTR_RATIO = float(INTR_RATIO)
    ROTA_THRESH = ARGS.rotation_threshold
    PADDING = ARGS.padding

    if os.path.isfile(PATH_OCR) and os.path.isfile(PATH_IMG):
        print(f"[INFO ] generate trainingsets from single file '{PATH_OCR}'")
        print(f"[DEBUG] args: {ARGS}")
        TRAINING_DATA = TrainingSets(PATH_OCR, PATH_IMG)
        RESULT = TRAINING_DATA.create(
            output_prefix=OUTPUT_PREFIX,
            min_chars=MIN_CHARS,
            summary=SUMMARY,
            reorder=REORDER,
            intrusion_ratio=INTR_RATIO,
            rotation_threshold=ROTA_THRESH,
            binarize=BINARIZE,
            sanitize=SANITIZE,
            padding=PADDING)
        print(f"[DONE ] got '{len(RESULT)}' pairs from '{PATH_OCR}'"
              f" and '{PATH_IMG}' in '{TRAINING_DATA.label}', please review")
    # if os.path.isdir(PATH_OCR) and os.path.isdir(PATH_IMG):
    #   TODO handle lists of inputs
    #   print(f"[INFO ] inspect OCR-dir '{PATH_OCR}' and image dir '{PATH_IMG}")
    else:
        print(f"[ERROR  ] invalid OCR '{PATH_OCR}' or Image '{PATH_IMG}'!")


if __name__ == "__main__":
    main()
