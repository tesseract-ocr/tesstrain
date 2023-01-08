# tesstrain.py

Utilities for working with Tesseract >= 4 using artificial training data.

## Install

This package requires the Tesseract training tools to be available on your system.

To install the PIP package, either use `pip install tesstrain` (for existing packages) or `pip install .` (from source checkout).
A supported Python version (at least 3.7) is required for running.

## Running

* Use the terminal interface to directly interact with the tools: `python -m tesstrain --help`.
* Call it from your own code using the high-level interface `tesstrain.run()`.

## License

Software is provided under the terms of the `Apache 2.0` license.

Sample training data provided by [Deutsches Textarchiv](https://deutschestextarchiv.de) is [in the public domain](http://creativecommons.org/publicdomain/mark/1.0/).
