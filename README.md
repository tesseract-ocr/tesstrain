# tesstrain

> Training workflow for Tesseract 5 as a Makefile for dependency tracking.

## Install

### Auxiliaries

You will need at least GNU `make` (minimal version 4.2), `wget`, `find`, `bash`, `unzip` and `bc`.

### Leptonica, Tesseract

You will need a recent version (>= 5.3) of tesseract built with the
training tools and matching leptonica bindings.
[Build](https://tesseract-ocr.github.io/tessdoc/Compiling)
[instructions](https://tesseract-ocr.github.io/tessdoc/Compiling-%E2%80%93-GitInstallation)
and more can be found in the [Tesseract User Manual](https://tesseract-ocr.github.io/tessdoc/).

#### Windows

  1. Install the latest tesseract (e.g. from https://digi.bib.uni-mannheim.de/tesseract/), make sure that tesseract is added to your PATH.
  2. Install [Python 3](https://www.python.org/downloads/)
  3. Install [Git SCM to Windows](https://gitforwindows.org/) - it provides a lot of linux utilities on Windows (e.g. `find`, `unzip`, `rm`) and put `C:\Program Files\Git\usr\bin` to the beginning of your PATH variable (temporarily you can do it in `cmd` with `set PATH=C:\Program Files\Git\usr\bin;%PATH%` - unfortunately there are several Windows tools with the same name as on linux (`find`, `sort`) with different behaviour/functionality and there is need to avoid them during training.
  4. Install winget/[Windows Package Manager](https://github.com/microsoft/winget-cli/releases/) and then run `winget install GnuWin32.Make` and `winget install wget` to install missing tools.
  5. Download [Bc and dc calculator in Windows](https://embedeo.org/ws/command_line/bc_dc_calculator_windows/) and unzip bc.exe somewhere to your path (e.g. in my case `unzip -j bc-1.07.1-win32-embedeo-02.zip "bc-1.07.1-win32-embedeo-02/bin/bc.exe" -d "c:\Program Files\Tools"`)

### Python

You need a recent version of Python 3.x. For image processing the Python library `Pillow` is used.
If you don't have a global installation, please use the provided requirements file `pip install -r requirements.txt`.


### Language data

Tesseract expects some configuration data (a file `radical-stroke.txt` and `*.unicharset` for all scripts) in `DATA_DIR`.
To fetch them:

    make tesseract-langdata

(This step is only needed once and already included implicitly in the `training` target,
but you might want to run explicitly it in advance.)


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

Run

    make training MODEL_NAME=name-of-the-resulting-model


which is basically a shortcut for

    make unicharset lists proto-model tesseract-langdata training


Run `make help` to see all the possible targets and variables:

<!-- BEGIN-EVAL -w '```' '```' -- make help -->
```

  Targets

    unicharset       Create unicharset
    charfreq         Show character histogram
    lists            Create lists of lstmf filenames for training and eval
    training         Start training
    traineddata      Create best and fast .traineddata files from each .checkpoint file
    proto-model      Build the proto model
    tesseract-langdata  Download stock unicharsets
    clean            Clean all generated files

  Variables

    MODEL_NAME         Name of the model to be built. Default: foo
    START_MODEL        Name of the model to continue from. Default: ''
    PROTO_MODEL        Name of the proto model. Default: OUTPUT_DIR/MODEL_NAME.traineddata
    WORDLIST_FILE      Optional file for dictionary DAWG. Default: OUTPUT_DIR/MODEL_NAME.wordlist
    NUMBERS_FILE       Optional file for number patterns DAWG. Default: OUTPUT_DIR/MODEL_NAME.numbers
    PUNC_FILE          Optional file for punctuation DAWG. Default: OUTPUT_DIR/MODEL_NAME.punc
    DATA_DIR           Data directory for output files, proto model, start model, etc. Default: data
    OUTPUT_DIR         Output directory for generated files. Default: DATA_DIR/MODEL_NAME
    GROUND_TRUTH_DIR   Ground truth directory. Default: OUTPUT_DIR-ground-truth
    TESSDATA_REPO      Tesseract model repo to use (_fast or _best). Default: _best
    TESSDATA           Path to the .traineddata directory to start finetuning from. Default: ./usr/share/tessdata
    MAX_ITERATIONS     Max iterations. Default: 10000
    EPOCHS             Set max iterations based on the number of lines for training. Default: none
    DEBUG_INTERVAL     Debug Interval. Default:  0
    LEARNING_RATE      Learning rate. Default: 0.0001 with START_MODEL, otherwise 0.002
    NET_SPEC           Network specification. Default: [1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c\#\#\#]
    FINETUNE_TYPE      Finetune Training Type - Impact, Plus, Layer or blank. Default: ''
    LANG_TYPE          Language Type - Indic, RTL or blank. Default: ''
    PSM                Page segmentation mode. Default: 13
    RANDOM_SEED        Random seed for shuffling of the training data. Default: 0
    RATIO_TRAIN        Ratio of train / eval training data. Default: 0.90
    TARGET_ERROR_RATE  Stop training if the character error rate (CER in percent) gets below this value. Default: 0.01
```

<!-- END-EVAL -->

### Change directory assumptions

To override the default path name requirements, just set the respective variables in the above list:

    make training MODEL_NAME=name-of-the-resulting-model DATA_DIR=/data GROUND_TRUTH_DIR=/data/GT

If you want to use shell variables to override the make variables (for example because
you are running tesstrain from a script or other makefile), then you can use the `-e` flag:

    MODEL_NAME=name-of-the-resulting-model DATA_DIR=/data GROUND_TRUTH_DIR=/data/GT make -e training

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

## Extract training data from ALTO/PAGE and images

tesstrain provides a utility `tesstrain-extract-sets` to generate pairs of text lines and corresponding line images from input data in the form of
[ALTO](https://www.loc.gov/standards/alto/) or
[PAGE-XML](https://github.com/PRImA-Research-Lab/PAGE-XML) files that represent scanned pages (complete or partial) with existing OCR.

To install `tesstrain-extract-sets`, first set up a virtual environment and install the project via `pip`:

```
# create virtual environment in subfolder "venv"
python3 -m venv venv
# unix
source venv/bin/activate
# win
venv\Scripts\activate.bat

# actual install 
pip install .
```

`tesstrain-extract-sets` currently supports OCR data in ALTO V3, PAGE 2013 and PAGE 2019, as well as TIFF, JPEG and PNG images.

Output is written as UTF-8 encoded plain text files and TIFF images. The image frame is produced from the textline coordinates in the OCR data, so please take care of properly annotated geometrical information. Additionally, the tool can add a fixed synthetic padding around the textline or store it binarized (`--binarize`).

By default, several sanitize actions are performed at image line level, like deskewing or removement of top-bottom intruders. To disable this, add flag `--no-sanitze`. 

See `tesstrain-extract-sets --help` for a brief listing of all supported command line flags and options.

**NOTE:** The text of the lines is extracted as-is, no automatic correction takes place. It is strongly recommended to review the generated data before training Tesseract with it.


## License

Software is provided under the terms of the `Apache 2.0` license.

Sample training data provided by [Deutsches Textarchiv](https://deutschestextarchiv.de) is [in the public domain](http://creativecommons.org/publicdomain/mark/1.0/).
