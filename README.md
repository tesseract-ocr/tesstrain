# tesstrain

> Training workflow for Tesseract 4 as a Makefile for dependency tracking and building the required software from source.

## Install

### leptonica, tesseract

You will need a recent version (>= 4.0.0beta1) of tesseract built with the
training tools and matching leptonica bindings.
[Build](https://github.com/tesseract-ocr/tesseract/wiki/Compiling)
[instructions](https://github.com/tesseract-ocr/tesseract/wiki/Compiling-%E2%80%93-GitInstallation)
and more can be found in the [Tesseract project
wiki](https://github.com/tesseract-ocr/tesseract/wiki/).

Alternatively, you can build leptonica and tesseract within this project and install it to a subdirectory `./usr` in the repo:

```sh
  make leptonica tesseract
```

Tesseract will be built from the git repository, which requires CMake,
autotools (including autotools-archive) and some additional libraries for the
training tools. See the [installation notes in the tesseract
repository](https://github.com/tesseract-ocr/tesseract/blob/master/INSTALL.GIT.md).

### Python

You need a recent version of Python 3.x. For image processing the Python library `Pillow` is used.
If you don't have a global installation, please use the provided requirements file `pip install -r requirements.txt`.

<!-- radical-stroke will be fetched as requirement to proto-model, kba Wed Jan 30 10:58:10 CET 2019

### language data

Tesseract expects some configuration data (a file `fadical-stroke.txt`). To fetch it:

``` sh
  make langdata
```

-->

## Choose model name

Choose a name for your model. By convention, Tesseract stack models including
language-specific resources use (lowercase) three-letter codes defined in
[ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) with additional
information separated by underscore. E.g., `chi_tra_vert` for **tra**ditional
Chinese with **vert**ical typesetting. Language-independent (i.e. script-specific)
models use the capitalized name of the script type as identifier. E.g.,
`Hangul_vert` for Hangul script with vertical typesetting. In the following,
the model name is referenced by `MODEL_NAME`.

## Provide ground truth

Place ground truth consisting of line images and transcriptions in the folder
`data/MODEL_NAME-ground-truth`. This list of files will be split into training and
evaluation data, the ratio is defined by the `RATIO_TRAIN` variable.

Images must be TIFF and have the extension `.tif` or PNG and have the
extension `.png`, `.bin.png` or `.nrm.png`.

Transcriptions must be single-line plain text and have the same name as the
line image but with the image extension replaced by `.gt.txt`.

The repository contains a ZIP archive with sample ground truth, see
[ocrd-testset.zip](./ocrd-testset.zip). Extract it to `./data/foo-ground-truth` and run
`make training`.

**NOTE:** If you want to generate line images for transcription from a full
page, see tips in [issue 7](https://github.com/OCR-D/ocrd-train/issues/7) and
in particular [@Shreeshrii's shell
script](https://github.com/OCR-D/ocrd-train/issues/7#issuecomment-419714852).

## Train

```
 make training MODEL_NAME=name-of-the-resulting-model
```

which is basically a shortcut for

```
   make unicharset lists proto-model training
```

Run `make help` to see all the possible targets and variables:

<!-- BEGIN-EVAL -w '```' '```' -- make help -->
```

  Targets

    unicharset       Create unicharset
    lists            Create lists of lstmf filenames for training and eval
    training         Start training
    traineddata      Create best and fast .traineddata files from each .checkpoint file
    proto-model      Build the proto model
    leptonica        Build leptonica
    tesseract        Build tesseract
    tesseract-langs  Download tesseract-langs
    clean            Clean all generated files

  Variables

    MODEL_NAME         Name of the model to be built. Default: foo
    START_MODEL        Name of the model to continue from. Default: ''
    PROTO_MODEL        Name of the proto model. Default: 'data/foo/foo.traineddata'
    CORES              No of cores to use for compiling leptonica/tesseract. Default: 4
    LEPTONICA_VERSION  Leptonica version. Default: 1.78.0
    TESSERACT_VERSION  Tesseract commit. Default: 4.1.0
    TESSDATA_REPO      Tesseract model repo to use. Default: _best
    TESSDATA           Path to the .traineddata directory to start finetuning from. Default: ./usr/share/tessdata
    GROUND_TRUTH_DIR   Ground truth directory. Default: data/MODEL_NAME-ground-truth
    OUTPUT_DIR         Output directory for generated files. Default: data/MODEL_NAME
    MAX_ITERATIONS     Max iterations. Default: 10000
    LEARNING_RATE      Learning rate. Default: 0.0001 with START_MODEL, otherwise 0.002
    NET_SPEC           Network specification. Default: [1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c\#\#\#]
    FINETUNE_TYPE      Finetune Training Type - Impact, Plus, Layer or blank. Default: ''
    LANG_TYPE          Language Type - Indic, RTL or blank. Default: ''
    PSM                Page segmentation mode. Default: 6
    RANDOM_SEED        Random seed for shuffling of the training data. Default: 0
    RATIO_TRAIN        Ratio of train / eval training data. Default: 0.90
    TARGET_ERROR_RATE  Stop training if the character error rate (CER in percent) gets below this value. Default: 0.01
```

<!-- END-EVAL -->

### Make model files (traineddata)

When the training is finished, it will write a `traineddata` file which can be used
for text recognition with Tesseract. Note that this file does not include a
dictionary. The `tesseract` executable therefore prints an warning.

It is also possible to create additional `traineddata` files from intermediate
training results (the so called checkpoints). This can even be done while the
training is still running. Example:

    # Add MODEL_NAME and OUTPUT_DIR like for the training.
    make traineddata

This will create two directories `tessdata_best` and `tessdata_fast` in `OUTPUT_DIR`
with a best (double based) and fast (int based) model for each checkpoint.

It is also possible to create models for selected checkpoints only. Examples:

    # Make traineddata for the checkpoint files of the last three weeks.
    make traineddata CHECKPOINT_FILES="$(find data/foo -name '*.checkpoint' -mtime -21)"

    # Make traineddata for the last two checkpoint files.
    make traineddata CHECKPOINT_FILES="$(ls -t data/foo/checkpoints/*.checkpoint | head -2)"

    # Make traineddata for all checkpoint files with CER better than 1 %.
    make traineddata CHECKPOINT_FILES="$(ls data/foo/checkpoints/*[^1-9]0.*.checkpoint)"

Add `MODEL_NAME` and `OUTPUT_DIR` and replace `data/foo` by the output directory if needed.

## Plotting CER (experimental)

Training and Evaluation CER can be plotted using matplotlib. A couple of scripts are provided
as a starting point in `plot` subdirectory for plotting of different training scenarios. The training
log is expected to be saved in `plot/TESSTRAIN.LOG`.

As an example, use the training data provided in 
[ocrd-testset.zip](./ocrd-testset.zip) to do training and generate the plots.
Plotting can be done while training is running also to depict the training status till then.
```
unzip ocrd-testset.zip -d data/ocrd-ground-truth
nohup make training MODEL_NAME=ocrd START_MODEL=frk TESSDATA=~/tessdata_best MAX_ITERATIONS=10000 > plot/TESSTRAIN.LOG &
```
```
cd ./plot
./plot_cer.sh 
```

## Generate training data from ALTO/PAGE

tesstrain provides a utility `tesstrain-extract-gt` to generate pairs of text
line and corresponding line images from input data in the form of
[ALTO](https://www.loc.gov/standards/alto/) or
[PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) files that represent
scanned pages (complete or partial) with existing OCR.

To install the `tesstrain-extract-gt` tool, set up a virtual environment and install the project with `pip`:

```
# create virtual environment in subfolder "venv"
python3 -m venv venv
# unix
source venv/bin/activate
# win
venv\Scripts\activate.bat

pip install -U pip
pip install .
```

`tesstrain-extract-gt` currently supports ALTO V3, PAGE 2013 and PAGE 2019 as
OCR formats and TIFF, JPEG and PNG images.

Output is written as UTF-8 encoded plain text files and TIFF images.

See `tesstrain-extract-gt --help` for a brief listing of all supported command
line flags and options.

**NOTE:** The text of the lines is extracted as-is, no automatic correction
takes place. Therefore, it is required to manually review the generated data
before training Tesseract with it.


## License

Software is provided under the terms of the `Apache 2.0` license.

Sample training data provided by [Deutsches Textarchiv](https://deutschestextarchiv.de) is [in the public domain](http://creativecommons.org/publicdomain/mark/1.0/).
