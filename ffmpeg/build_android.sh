#!/bin/bash
######################################################
# Usage:
# put this script in top of FFmpeg source tree
# ./build_android
# It generates binary for following architectures:
# ARMv6 
# ARMv6+VFP 
# ARMv7+VFPv3-d16 (Tegra2) 
# ARMv7+Neon (Cortex-A8)
# Customizing:
# 1. Feel free to change ./configure parameters for more features
# 2. To adapt other ARM variants
# set $CPU and $OPTIMIZE_CFLAGS 
# call build_one
######################################################
SPEC_ONE=arm
GO_ARM=no
GO_X86=yes
GO_X64=no
NDK=~/Library/Android/sdk/ndk-bundle
PLATFORM=$NDK/platforms/android-21/arch-arm
PREBUILT=$NDK/toolchains/llvm/prebuilt/darwin-x86_64
LDEXTRAS="-Wl,-rpath-link=$PLATFORM/usr/lib -L$PLATFORM/usr/lib -nostdlib -lc -lm -ldl -llog"
EXTRA_CXXFLAGS="-Wno-multichar -Wno-psabi -fno-exceptions -fno-rtti"
CLANG=$PREBUILT/bin/clang
function build_one
{
LDEXTRAS="-Wl,-rpath-link=$PLATFORM/usr/lib -L$PREBUILT/lib/gcc/$PREARCH/4.9.x -L$PLATFORM/usr/lib -nostdlib -lc -lm -ldl -llog"

./configure --target-os=linux \
    --prefix=$PREFIX \
    --enable-cross-compile \
    --extra-libs="-lgcc" \
    --arch=$ARCH \
    --cc=$CLANG \
    --cross-prefix=$PREBUILT/bin/$PREARCH- \
    --nm=$PREBUILT/bin/$PREARCH-nm \
    --sysroot=$PLATFORM \
    --extra-cflags=" -O3 -fpic -DANDROID -DHAVE_SYS_UIO_H=1 -Dipv6mr_interface=ipv6mr_ifindex -fasm -Wno-psabi -fno-short-enums -fno-strict-aliasing -finline-limit=300 $OPTIMIZE_CFLAGS " \
    --disable-shared \
    --enable-static \
    --extra-ldflags="$LDEXTRAS" \
    --extra-cxxflags="$EXTRA_CXXFLAGS" \
    --disable-everything \
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
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=g723_1 \
    --enable-decoder=g723_1 \
    $ADDITIONAL_CONFIGURE_FLAG

make clean
make
make  -j4 install
$PREBUILT/bin/$PREARCH-ar d libavcodec/libavcodec.a inverse.o
if [ $ARCH == 'x86' ] || [ $ARCH == 'x86_64' ]
then
$PREBUILT/bin/$PREARCH-ld -rpath-link=$PLATFORM/usr/lib -L$PLATFORM/usr/lib  -soname libffmpeg.so -shared -Bsymbolic --whole-archive --no-undefined -o libavcodec/libavcodec.a libavformat/libavformat.a libavutil/libavutil.a libswscale/libswscale.a -lc -lm -lz -ldl -llog --dynamic-linker=/system/bin/linker $PREBUILT/lib/gcc/$PREARCH/4.9/libgcc.a;
else
$PREBUILT/bin/$PREARCH-ld -rpath-link=$PLATFORM/usr/lib -L$PLATFORM/usr/lib  -soname libffmpeg.so -shared -nostdlib  -z,noexecstack -Bsymbolic --whole-archive --no-undefined -o libavcodec/libavcodec.a libavformat/libavformat.a libavutil/libavutil.a libswscale/libswscale.a -lc -lm -lz -ldl -llog --dynamic-linker=/system/bin/linker $PREBUILT/lib/gcc/$PREARCH/4.9/libgcc.a;
fi
}

if [ $SPEC_ONE != 'arm' ]
then
echo "ARM compile is not specified"
GO_ARM=no;
GO_X86=yes;
fi

if [ $SPEC_ONE != 'x86' ]
then
echo "X86 compile is not specified"
GO_X86=no;
GO_ARM=yes;
fi

if [ $GO_ARM == 'yes' ]
then
echo "ARM6 compiling"
#arm v6
ARCH=arm
PREARCH=arm-linux-androideabi
CLANG=$PREBUILT/bin/armv7a-linux-androideabi21-clang
CPU=armv6
OPTIMIZE_CFLAGS="-marm -march=$CPU"
PREFIX=./android/$CPU 
ADDITIONAL_CONFIGURE_FLAG=
build_one;
fi

if [ $GO_ARM == 'yes' ]
then
echo "ARM7 compiling"
#arm v7vfpv3
ARCH=arm
PREARCH=arm-linux-androideabi
CLANG=$PREBUILT/bin/armv7a-linux-androideabi21-clang
CPU=armv7-a
OPTIMIZE_CFLAGS="-mfloat-abi=softfp -mfpu=vfpv3-d16 -marm -march=$CPU "
PREFIX=./android/$CPU
ADDITIONAL_CONFIGURE_FLAG=
build_one;
fi

if [ $GO_ARM == 'yes' ]
then
echo "ARM64 compiling"
#arm v8a
ARCH=arm
PREARCH=arm-linux-androideabi
PLATFORM=$NDK/platforms/android-21/arch-arm64
CLANG=$PREBUILT/bin/armv7a-linux-androideabi21-clang
CPU=armv64-v8a
OPTIMIZE_CFLAGS="-mfloat-abi=softfp -mfpu=vfpv3-d16 -marm -march=$CPU "
PREFIX=./android/$CPU
ADDITIONAL_CONFIGURE_FLAG=
build_one;
fi

if [ $GO_X86 == 'yes' ]
then
echo "x86 compiling"
#x86
PLATFORM=$NDK/platforms/android-14/arch-x86
PREBUILT=$NDK/toolchains/x86-4.6/prebuilt/linux-x86_64
LDEXTRAS="-Wl,-rpath-link=$PLATFORM/usr/lib -L$PLATFORM/usr/lib -lc -lm -ldl -llog"
ARCH=x86
PREARCH=i686-linux-android
CPU=x86
OPTIMIZE_CFLAGS="-march=$CPU"
PREFIX=./android/$CPU
ADDITIONAL_CONFIGURE_FLAG=
build_one;
fi

if [ $GO_X64 == 'yes' ]
then
echo "x64 compiling"
#x86
PLATFORM=$NDK/platforms/android-21/arch-x86_64
PREBUILT=$NDK/toolchains/x86_64-4.9/prebuilt/linux-x86_64
LDEXTRAS="-Wl,-rpath-link=$PLATFORM/usr/lib -L$PLATFORM/usr/lib -lc -lm -ldl -llog"
ARCH=x86_64
PREARCH=x86_64-linux-android
CPU=x86_64
OPTIMIZE_CFLAGS="-march=$CPU"
PREFIX=./android/$CPU
ADDITIONAL_CONFIGURE_FLAG=
build_one;
fi

#arm v7vfp
#CPU=armv7-a
#OPTIMIZE_CFLAGS="-mfloat-abi=softfp -mfpu=vfp -marm -march=$CPU "
#PREFIX=./android/$CPU-vfp
#ADDITIONAL_CONFIGURE_FLAG=
#build_one

#arm v7n
#CPU=armv7-a
#OPTIMIZE_CFLAGS="-mfloat-abi=softfp -mfpu=neon -marm -march=$CPU -mtune=cortex-a8"
#PREFIX=./android/$CPU 
#ADDITIONAL_CONFIGURE_FLAG=--enable-neon
#build_one

#arm v6+vfp
#CPU=armv6
#OPTIMIZE_CFLAGS="-DCMP_HAVE_VFP -mfloat-abi=softfp -mfpu=vfp -marm -march=$CPU"
#PREFIX=./android/${CPU}_vfp 
#ADDITIONAL_CONFIGURE_FLAG=
#build_one
