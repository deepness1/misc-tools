#!/bin/zsh

set -e

if [[ $# != 1 ]]; then
    echo "usage: fixwv.sh <file.wv>"
    exit 1
fi

src=$1
bak=$1.org
tmp=/tmp/${src:t}.wav
ftmp=/tmp/${src:t}-fix.wav

mv "$src" "$bak"
wvunpack "$bak" -o "$tmp"
ffmpeg -i "$tmp" -acodec copy "$ftmp"
wavpack -y -hh "$ftmp" -o "$src"
rm "$tmp" "$ftmp"
