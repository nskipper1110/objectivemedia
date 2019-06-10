LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

#TARGET_ARCH_ABI := armeabi-v7a
#TARGET_ARCH_ABI := armeabi-v7n
#TARGET_ARCH_ABI := armeabi
TARGET_ARCH_ABI := arm64-v8a
#TARGET_ARCH_ABI := x86
#TARGET_ARCH_ABI := x86_64
#TARGET_ARCH_ABI :=  mips
#TARGET_ARCH_ABI := mips64

TARGET_ARCH := arm64
#TARGET_ARCH := arm
#TARGET_ARCH := x86

LOCAL_MODULE    := objectivemedia
LOCAL_SRC_FILES := \
		   ../dbg.cpp \
		   ../platform/platform_devices.cpp \
		   ../platform/platform_codecs.cpp \
		   com_mti_primitives_codecs_G7231AudioDecoder.cpp \
		   com_mti_primitives_codecs_G7231AudioEncoder.cpp \
		   com_mti_primitives_codecs_H263VideoDecoder.cpp \
		   com_mti_primitives_codecs_H263VideoEncoder.cpp \
		   com_mti_primitives_devices_VideoInputDevice.cpp \
		   
	
LOCAL_C_INCLUDES := $(LOCAL_PATH)/android/ffmpeg-build/$(TARGET_ARCH_ABI)/include $(LOCAL_PATH)/../platform

LOCAL_LDLIBS := -L$(NDK_PLATFORMS_ROOT)/$(TARGET_PLATFORM)/arch-$(TARGET_ARCH)/usr/lib \
                -L$(LOCAL_PATH)/android/ffmpeg-build/$(TARGET_ARCH_ABI)/lib \
                -lavformat \
                -lavcodec \
                -lavdevice \
                -lavfilter \
                -lavutil \
                -lswscale \
                -llog \
                -lz \
                -ldl \
                -lgcc

LOCAL_CFLAGS := -D__STDC_CONSTANT_MACROS
LOCAL_CPP_FEATURES += exceptions
LOCAL_CPPFLAGS += -fexceptions

include $(BUILD_SHARED_LIBRARY)

