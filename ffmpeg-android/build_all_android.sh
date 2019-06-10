#!/bin/bash
export NDK=~/android-ndk-r15c
CHIP=arm
BUILDROOT=`(pwd)`
./build_ffmpeg.sh $CHIP full $BUILDROOT/build $BUILDROOT/dst/$CHIP
CHIP=armv7-a
./build_ffmpeg.sh $CHIP full $BUILDROOT/build $BUILDROOT/dst/$CHIP
CHIP=arm-v7n
./build_ffmpeg.sh $CHIP full $BUILDROOT/build $BUILDROOT/dst/$CHIP
CHIP=arm64-v8a
./build_ffmpeg.sh $CHIP full $BUILDROOT/build $BUILDROOT/dst/$CHIP
CHIP=x86_64
./build_ffmpeg.sh $CHIP full $BUILDROOT/build $BUILDROOT/dst/$CHIP