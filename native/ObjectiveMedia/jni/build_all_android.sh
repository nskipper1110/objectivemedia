#!/bin/bash
export NDK=~/android-ndk-r19c
JNIROOT=`(pwd)`
BUILDROOT=`(pwd)`/../

#architectures:
#arm
#armv7a
#armv7n
#arm64
# cd $BUILDROOT
# ARCH=arm
# cp -Rf $JNIROOT/Android_$ARCH.mk $JNIROOT/Android.mk
# cp -Rf $JNIROOT/Application_$ARCH.mk $JNIROOT/Application.mk
# $NDK/ndk-build

ARCH=armv7a
cp -Rf $JNIROOT/Android_$ARCH.mk $JNIROOT/Android.mk
cp -Rf $JNIROOT/Application_$ARCH.mk $JNIROOT/Application.mk
$NDK/ndk-build

# ARCH=armv7n
# cp -Rf $JNIROOT/Android_$ARCH.mk $JNIROOT/Android.mk
# cp -Rf $JNIROOT/Application_$ARCH.mk $JNIROOT/Application.mk
# $NDK/ndk-build

ARCH=arm64
cp -Rf $JNIROOT/Android_$ARCH.mk $JNIROOT/Android.mk
cp -Rf $JNIROOT/Application_$ARCH.mk $JNIROOT/Application.mk
$NDK/ndk-build