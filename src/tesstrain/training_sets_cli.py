# -*- coding: utf-8 -*-
"""Generate Sets of Training Data TextLine + Image Pairs"""

import os

from argparse import (
    ArgumentParser,
    Namespace,
)
from pathlib import (
    Path
)

from tesstrain.training_sets import (
    DEFAULT_OUTDIR_PREFIX,
    DEFAULT_MIN_CHARS,
    DEFAULT_USE_SUMMARY,
    DEFAULT_USE_REORDER,
    DEFAULT_INTRUSION_RATIO,
    DEFAULT_ROTATION_THRESH,
    DEFAULT_SANITIZE,
    DEFAULT_BINARIZE,
    DEFAULT_PADDING,
    SUFFIX_SUMMARY,
    TrainingSets,
)


def _run_single_page(args: Namespace):
    path_ocr = os.path.abspath(args.data)
    path_img = os.path.abspath(args.image)
    output_dir = os.path.abspath(args.output_dir)
    min_chars = args.minchars
    do_summary = args.summary
    do_reorder = args.reorder
    do_binarize = args.binarize
    do_opt = args.sanitize
    intrusion_ratio = args.intrusion_ratio
    if isinstance(intrusion_ratio, str) and ',' in intrusion_ratio:
        intrusion_ratio = [float(n) for n in intrusion_ratio.split(',')]
    else:
        intrusion_ratio = float(intrusion_ratio)
    rotation_thresh = args.rotation_threshold
    padding = args.padding
    intrusion_ratio = args.intrusion_ratio
    if isinstance(intrusion_ratio, str) and ',' in intrusion_ratio:
        intrusion_ratio = [float(n) for n in intrusion_ratio.split(',')]
    else:
        intrusion_ratio = float(intrusion_ratio)
    _t_sets = TrainingSets(path_ocr, path_img, output_dir=output_dir)
    prefix_output = args.prefix_output
    if prefix_output:
        _t_sets.pair_prefix = prefix_output
    res = _t_sets.create(
        min_chars=min_chars,
        summary=do_summary,
        reorder=do_reorder,
        intrusion_ratio=intrusion_ratio,
        rotation_threshold=rotation_thresh,
        binarize=do_binarize,
        sanitize=do_opt,
        padding=padding)
    print(f"[DEBUG] got '{len(res)}' pairs from '{path_ocr}'"
            f" and '{path_img}' in '{output_dir}', better review")
    return len(res)


def _run_dir(args):
    path_ocr_dir = args.data
    path_img_dir = args.image
    _all_ocrs = sorted([os.path.join(path_ocr_dir, _f)
                 for _f in os.listdir(path_ocr_dir)
                 if str(_f).endswith('.xml')])
    print(f"[DEBUG] found total {len(_all_ocrs)} OCR files in {path_ocr_dir} ")
    _n_pairs = 0
    _misses = []
    for _an_ocr in _all_ocrs:
        _ocr_label = Path(_an_ocr).stem
        _img_match = __get_image(path_img_dir, _ocr_label)
        if _img_match:
            args.data = _an_ocr
            args.image = _img_match
            _n_pairs += _run_single_page(args)
        else:
            print(f"[WARNING] no img for {_ocr_label}")
            _misses.append(_an_ocr)
    print(f"[INFO] created {_n_pairs} pairs, missed {len(_misses)} in {path_img_dir}")


def __get_image(path_image_dir, label):
    _all_imgs = [os.path.join(path_image_dir, _f) 
                 for _f in os.listdir(path_image_dir)
                 if __has_image_ext(_f) and Path(_f).stem == label]
    if not _all_imgs:
        return None
    if len(_all_imgs) > 1:
        raise RuntimeError(f"Invalid image match {_all_imgs} for {label}")
    return _all_imgs[0]


def __has_image_ext(file_name:str) -> bool:
    _ext:str = Path(file_name).suffix
    return _ext in ['.jpg', '.tif','.png']



########
# MAIN #
########
def main():
    PARSER: ArgumentParser = ArgumentParser(description="generate pairs of textlines and image frames from existing OCR and image data")
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
        "--output_dir",
        default=DEFAULT_OUTDIR_PREFIX,
        help=f"output directory, re-created if already exists. (default: <script-dir>/<{DEFAULT_OUTDIR_PREFIX}>)")
    PARSER.add_argument(
        "--prefix-output",
        required=False,
        help="optional: prefix each pair using this arg. (default: '')")
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
        help=f"optional: print all lines in additional file (default: {DEFAULT_USE_SUMMARY}, pattern: <default-output-dir>{SUFFIX_SUMMARY})")
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

    ARGS: Namespace = PARSER.parse_args()
    print(f"[DEBUG] {os.path.basename(__file__)} using args: {ARGS}")
    PATH_OCR = ARGS.data
    PATH_IMG = ARGS.image

    if os.path.isfile(PATH_OCR) and os.path.isfile(PATH_IMG):
        print(f"[INFO ] generate trainingsets from single file '{PATH_OCR}'")
        _run_single_page(ARGS)
    elif os.path.isdir(PATH_OCR) and os.path.isdir(PATH_IMG):
        _run_dir(ARGS)
        print(f"[INFO ] inspect OCR-dir '{PATH_OCR}' and image dir '{PATH_IMG}")
    else:
        print(f"[ERROR  ] invalid OCR '{PATH_OCR}' or Image '{PATH_IMG}'!")


if __name__ == "__main__":
    main()
