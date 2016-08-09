#!/bin/bash
#Linux x86 FFMPEG configure command
./configure \
    --prefix=./build/linux/x86 \
    --disable-shared \
    --enable-static \
    --disable-ffmpeg \
    --disable-ffplay \
    --disable-ffprobe \
    --disable-ffserver \
    --disable-everything \
    --disable-muxers \
    --disable-demuxers \
    --disable-parsers \
    --disable-filters \
    --disable-hwaccels \
    --enable-decoder=rawvideo \
    --enable-encoder=rawvideo \
    --enable-decoder=mjpeg \
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=g723_1 \
    --enable-decoder=g723_1 \
    --enable-indev=v4l2 \
    --target-os=linux \
    --arch=i386 \
    --cc="gcc -m32"
make clean
make
make install

#Linux x64 FFMPEG configure command
./configure \
    --prefix=./build/linux/x64 \
    --disable-shared \
    --enable-static \
    --disable-ffmpeg \
    --disable-ffplay \
    --disable-ffprobe \
    --disable-ffserver \
    --disable-everything \
    --disable-muxers \
    --disable-demuxers \
    --disable-parsers \
    --disable-filters \
    --disable-hwaccels \
    --enable-decoder=rawvideo \
    --enable-encoder=rawvideo \
    --enable-decoder=mjpeg \
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=g723_1 \
    --enable-decoder=g723_1 \
    --enable-indev=v4l2 \
    --target-os=linux \
    --arch=x86_64 \
    --cc="gcc -m64 -fPIC"
make clean
make
make install

