#!/usr/bin/bash

# convert svg file into png
# ./svg2png.sh language.svg 30
# 1: icon file
# 2: output size

# Test convert
if [[ -z $(which convert) ]]; then
    echo "[Error] imagemagick not installed!"
    exit 1
fi

icon_file="./icons/${1}"

# Test file exists
if [[ ! -f $icon_file ]]; then
    echo "[Error] File '${icon_file}' not found!"
    exit 1
fi

icon_name=$(basename $1)
png_file="./icons/${icon_name%.*}.png"
out_width=$2

if [[ $out_width -le 0 ]]; then
    echo "[Error] Minimun width size is 1px!"
    exit 1
fi

convert -background '#424242' -resize "${out_width}"x $icon_file $png_file