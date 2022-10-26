#!/bin/env bash

mkdir tmp &>/dev/null
cd tmp

grep -Po '(?<=img":\ ").*?(?=")' ../req.json | split -d -l 1

base64 -d x00 > img01.webp
base64 -d x01 > img02.webp
base64 -d x02 > img03.webp
base64 -d x03 > img04.webp

dwebp img01.webp -o 1.png &>/dev/null
dwebp img02.webp -o 2.png &>/dev/null
dwebp img03.webp -o 3.png &>/dev/null
dwebp img04.webp -o 4.png &>/dev/null

rm x00 x01 x02 x03 img01.webp img02.webp img03.webp img04.webp
