#!/bin/bash

rm -v $(find data/${1}/ -size 0 -name "*.box"|sed s/.box/.*/)
  my_files=$(find data/${1}/ -name "*.box")
    for my_file in ${my_files}; do
      python generate_gt_from_box.py -b ${my_file} -t ${my_file%.*}.gt.txt
	  sleep 1
 	  echo ${my_file}
	  touch ${my_file%.*}.tif
	  touch ${my_file%.*}.box
	  touch ${my_file%.*}.lstmf
    done
cd data/${1}/
    #for f in *.*; do pre="${f%.*}"; suf="${f##*.}";     mkdir -p "${pre//\.exp0.*/}"; mv -i -- "$f" "${pre//\.exp0\./\/}.${suf}"; done
	rm -v -rf tesstrain
	rm -v -rf eng
	rm -v tesstrain.log
cd ../..
