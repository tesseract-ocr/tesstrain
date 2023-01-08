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
#
# This script provides an easy way to execute various phases of training
# Tesseract.  For a detailed description of the phases, see
# https://tesseract-ocr.github.io/tessdoc/Training-Tesseract.html.

import logging

from tesstrain.arguments import (
    get_argument_parser,
    TrainingArguments,
    verify_parameters_and_handle_defaults
)
from tesstrain.generate import cleanup
from tesstrain.wrapper import run_from_context


log = logging.getLogger()


def setup_logging_console():
    log.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )
    console.setFormatter(console_formatter)
    log.addHandler(console)


def setup_logging_logfile(logfile):
    logfile = logging.FileHandler(logfile, encoding='utf-8')
    logfile.setLevel(logging.DEBUG)
    logfile_formatter = logging.Formatter(
        "[%(asctime)s] - %(levelname)s - %(name)s - %(message)s"
    )
    logfile.setFormatter(logfile_formatter)
    log.addHandler(logfile)
    return logfile


def parse_flags(argv=None):
    ctx = TrainingArguments()
    log.debug(ctx)
    parser = get_argument_parser()
    parser.parse_args(args=argv, namespace=ctx)
    return verify_parameters_and_handle_defaults(ctx)


def main():
    setup_logging_console()
    ctx = parse_flags()
    logfile = setup_logging_logfile(ctx.log_file)

    run_from_context(ctx)

    log.removeHandler(logfile)
    logfile.close()
    cleanup(ctx)
    log.info("All done!")
    return 0


if __name__ == '__main__':
    main()
