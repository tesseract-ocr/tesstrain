# (C) Copyright 2014, Google Inc.
# (C) Copyright 2018, James R Barlow
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Actual execution logic.
"""

import logging
import sys
from typing import List, Optional

from tesstrain import language_specific
from tesstrain.arguments import (
    TrainingArguments,
    verify_parameters_and_handle_defaults,
)
from tesstrain.generate import (
    cleanup,
    initialize_fontconfig,
    make_lstmdata,
    phase_E_extract_features,
    phase_I_generate_image,
    phase_UP_generate_unicharset,
)

log = logging.getLogger()


def run_from_context(ctx):
    if not ctx.linedata:
        log.error('--linedata_only is required since only LSTM is supported')
        sys.exit(1)

    log.info(f'=== Starting training for language {ctx.lang_code}')
    ctx = language_specific.set_lang_specific_parameters(ctx, ctx.lang_code)

    initialize_fontconfig(ctx)
    phase_I_generate_image(ctx, par_factor=8)
    phase_UP_generate_unicharset(ctx)

    if ctx.linedata:
        phase_E_extract_features(ctx, ['lstm.train'], 'lstmf')
        make_lstmdata(ctx)


def run(
    fonts: List[str],
    langdata_directory: str,
    maximum_pages: int,
    fonts_directory: Optional[str] = None,
    temporary_directory: Optional[str] = None,
    language_code: Optional[str] = None,
    output_directory: Optional[str] = None,
    overwrite: bool = False,  # TODO: Not required anymore.
    save_box_tiff: bool = False,
    linedata_only: bool = False,
    training_text: Optional[str] = None,
    wordlist_file: Optional[str] = None,
    extract_font_properties: bool = True,
    distort_image: bool = False,
    tessdata_directory: Optional[str] = None,
    exposures: Optional[List[int]] = None,
    point_size: int = 12,
):
    """
    :param fonts: A list of font names to train on. These need to be recognizable by
                  Pango using fontconfig. An easy way to list the canonical name of all
                  fonts available on your system is to run text2image with
                  `--list_available_fonts` and the appropriate `--fonts_dir` path.
    :param fonts_directory: Path to font files.
    :param temporary_directory: Path to temporary training directory.
    :param language_code: ISO 639 language code. Defaults to English.
    :param langdata_directory: Path to tesseract/training/langdata directory.
    :param maximum_pages: The maximum number of pages to generate.
    :param output_directory: Location of generated traineddata file.
    :param overwrite: Safe to overwrite files in output directory.
    :param save_box_tiff: Save box/tiff pairs along with lstmf files.
    :param linedata_only: Only generate training data for lstmtraining.
    :param training_text: File with the text to render and use for training. If
                          unspecified, we will look for it in the langdata
                          directory.
    :param wordlist_file: File with the word list for the language ordered by
                          decreasing frequency. If unspecified, we will look for it in
                          the langdata directory.
    :param extract_font_properties: Assumes that the input file contains a list of
                                    ngrams. Renders each ngram, extracts spacing
                                    properties and records them in a `.fontinfo` file.
    :param distort_image: Degrade rendered image with noise, blur, invert.
    :param tessdata_directory: Specify location of existing traineddata files,
                               required during feature extraction. If set, it should be
                               the path to the tesseract/tessdata directory. If
                               unspecified, the `TESSDATA_PREFIX` specified in the
                               current environment will be used.
    :param exposures: A list of exposure levels to use (e.g. `[-1, 0, 1]`). If
                      unspecified, language-specific ones will be used.
    :param point_size: Size of printed text.
    """
    ctx = TrainingArguments()
    ctx.fonts = fonts
    ctx.fonts_dir = fonts_directory if fonts_directory else ctx.fonts_dir
    ctx.tmp_dir = temporary_directory
    ctx.lang_code = language_code if language_code else ctx.lang_code
    ctx.langdata_dir = langdata_directory
    ctx.max_pages = maximum_pages
    ctx.output_dir = output_directory
    ctx.overwrite = overwrite
    ctx.save_box_tiff = save_box_tiff
    ctx.linedata = linedata_only
    ctx.training_text = training_text
    ctx.wordlist_file = wordlist_file
    ctx.extract_font_properties = extract_font_properties
    ctx.distort_image = distort_image
    ctx.tessdata_dir = tessdata_directory
    ctx.exposures = exposures
    ctx.ptsize = point_size

    verify_parameters_and_handle_defaults(ctx)

    run_from_context(ctx)
    cleanup(ctx)
    log.info('All done!')
    return 0
