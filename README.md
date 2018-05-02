<!-- BEGIN-MARKDOWN-TOC -->
* [Setup leptonica / tesseract](#setup-leptonica--tesseract)
* [1. Generierung Tif](#1-generierung-tif)
* [2. Generierung Box-Files](#2-generierung-box-files)
* [3. Generierung Codec](#3-generierung-codec)
* [4. Generierung lstmf-Files](#4-generierung-lstmf-files)
* [5. Generierung Proto-Modell](#5-generierung-proto-modell)
* [6. Aufteilung der Daten in Test und Train](#6-aufteilung-der-daten-in-test-und-train)
* [7. Modelltraining](#7-modelltraining)
* [8. Modellabschluss](#8-modellabschluss)
* [9. Erkennung der Testdaten](#9-erkennung-der-testdaten)

<!-- END-MARKDOWN-TOC -->

See also ocr-d.github.io/PhilTag-2018

## Build leptonica / tesseract

### Leptonica

```
mkdir -p _build
cd _build
wget http://www.leptonica.org/source/leptonica-1.75.3.tar.gz
tar xf leptonica-1.75.3.tar.gz
cd leptonica-1.75.3
./configure
make
sudo make install
```

### Tesseract

```
mkdir -p _build
cd _build
git clone --depth=1 https://github.com/tesseract-ocr/tesseract
cd tesseract
sh autogen.sh
./configure --prefix=/usr
make
make training
sudo make install training-install
```

https://bingrao.github.io/blog/post/2017/07/16/Install-Tesseract-4.0-in-ubuntun-16.04.html

## 1. Generierung Tif

  → convert

## 2. Generierung Box-Files

```bash
for y in `ls /home/binder/OCR/ocropus/fraktur_19jh/SELECTION-TRAIN/training/`; do
  echo $y
  for l in `ls /home/binder/OCR/ocropus/fraktur_19jh/SELECTION-TRAIN/training/$y/*.bin.png`;do
    base=`basename $l .bin.png`; echo "$y"_$base
    convert $l data/"$y"_$base.tif;
    python generate_line_box.py -i data/"$y"_$base.tif \
      -t /home/binder/OCR/ocropus/fraktur_19jh/SELECTION-TRAIN/training/"$y"/$base.gt.txt \
      > data/"$y"_$base.box; cp
    /home/binder/OCR/ocropus/fraktur_19jh/SELECTION-TRAIN/training/"$y"/$base.gt.txt data/"$y"_$base.gt.txt
  done
done
```

## 3. Generierung Codec

```sh
  /usr/local/bin/unicharset_extractor --output_unicharset springmann.unicharset --norm_mode 1 *.box
```

## 4. Generierung lstmf-Files

```sh
for i in `ls *.tif`;do
  base=`basename $i .tif`
  echo $base
  tesseract $i $base lstm.train
done
```

## 5. Generierung Proto-Modell

```sh
/usr/local/bin/combine_lang_model \
  --input_unicharset Fraktur.unicharset \
  --script_dir /home/kmw/built/langdata
  --output_dir tmp/ \
  --lang Fraktur
```

## 6. Aufteilung der Daten in Test und Train

```sh
  ls data/*.lstmf | sort -R > Fraktur.files.random.txt
  head -n 300 Fraktur.files.random.txt > Fraktur.test_files.txt
  tail -n +301 Fraktur.files.random.txt > Fraktur.training_files.txt
```

## 7. Modelltraining

**NOTE** `O1c61` bedeutet dass `61` Zeichen im Alphabet (Codec) sind.

```sh
lstmtraining \
  --traineddata tmp/Fraktur/Fraktur.traineddata \
  --net_spec '[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c61]' \
  --model_output out/base \
  --learning_rate 20e-4 \
  --train_listfile Fraktur.training_files.txt \
  --eval_listfile Fraktur.test_files.txt \
  --max_iterations 10000
```

## 8. Modellabschluss

```sh
lstmtraining \
  --stop_training \
  --continue_from out/base_checkpoint \
  --traineddata tmp/Fraktur/Fraktur.traineddata \
  --model_output out/Fraktur.traineddata
```

## 9. Erkennung der Testdaten

```sh
for i in `ls test/*.tif`;do
  base=`basename $i .tif`
  echo $base
  tesseract --tessdata-dir out/ -psm 13 -l Fraktur test/$base.tif test/$base
done
```
