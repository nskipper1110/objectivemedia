#!/bin/bash
 #Configure ANDROID_NDK environment variable
    ANDROID_NDK=~/android-ndk-r10d
    PATH=$PATH:$ANDROID_NDK

#5.  Setup the toolchain
    DEST=`pwd`
    PREFIX=$DEST/build/android/x86_64
    TOOLCHAIN=/tmp/vplayer
    $ANDROID_NDK/build/tools/make-standalone-toolchain.sh --toolchain=x86_64-4.9 --arch=x86_64 --system=linux-x86_64 --platform=android-21 --install-dir=/tmp/vplayer

    export PATH=$TOOLCHAIN/bin:$PATH
    export CC="ccache x86_64-linux-android-gcc-4.9"
    export LD=X86_64-linux-android-ld
    export AR=X86_64-linux-android-ar

#6.  Configure FFMPEG
./configure --target-os=linux --arch=x86_64 --cpu=x86_64 --cross-prefix=x86_64-linux-android- --enable-cross-compile --disable-shared --enable-static --disable-symver --disable-doc --disable-ffplay --disable-ffmpeg --disable-ffprobe --disable-ffserver --enable-version3 --disable-amd3dnow --disable-amd3dnowext --enable-asm --enable-yasm --enable-pic --prefix=$PREFIX --extra-cflags='-std=c99 -O3 -Wall -fpic -pipe   -DANDROID -DNDEBUG  -march=atom -msse3 -ffast-math -mfpmath=sse' --extra-ldflags='-lm -lz -Wl,--no-undefined -Wl,-z,noexecstack' \
    --disable-everything \
    --disable-muxers \
    --disable-demuxers \
    --disable-parsers \
    --disable-filters \
    --disable-hwaccels \
    --enable-decoder=rawvideo \
    --enable-encoder=rawvideo \
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=g723_1 \
    --enable-decoder=g723_1 \

make clean
make
make install
