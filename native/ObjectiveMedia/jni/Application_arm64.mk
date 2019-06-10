APP_PROJECT_PATH := $(call my-dir)/../
#APP_ABI := armeabi
#APP_ABI := armeabi-v7a
#APP_ABI := armeabi-v7n
#APP_ABI := x86
APP_ABI := arm64-v8a
#APP_ABI := x86_64
APP_STL := c++_static
APP_CPPFLAGS += -fexceptions
APP_CFLAGS += -Wno-error=format-security
