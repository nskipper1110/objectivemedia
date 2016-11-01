SHELL = /bin/sh
CC    = gcc
CCFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
CFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
CXXFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
LDFLAGS      = -Wl,--kill-at -shared -L/c/jdk/lib \
					   -L/c/jdk/lib/amd64 \
					   -L../../ffmpeg/build/win/x86/lib \
					   -lswscale \
					   -lswresample \
					   -lavcodec \
					   -lavfilter \
					   -lavformat \
					   -lavutil \
					   -lavdevice \
					   -lgcc \
					   -liconv \
					   -lstdc++ \
					   -lquartz \
					   -lstrmiids \
					   -lole32 \
					   -luuid
INCLUDES = -I/c/jdk/include \
		   -I/c/jdk/include/win32 \
		   -I../../ffmpeg/build/win/x86/include \
		   -I. \
		   -I./jni \
		   -I./platform

TARGET  = ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x86/objectivemedia_win32.dll
SOURCES = $(shell echo ./*.cpp) \
		  $(shell echo ./platform/*.cpp) \
		  $(shell echo ./jni/*.cpp)
#HEADERS = $(shell echo ./*.h) \
#		  $(shell echo ./jni/*.h) \
#		  $(shell echo ./platform/*.h)
OBJECTS = $(SOURCES:.cpp=.o)

CCFLAGS += $(INCLUDES)
CXXFLAGS += $(INCLUDES)
CFLAGS += $(INCLUDES)
all: $(TARGET)

clean:
	rm -f $(OBJECTS) $(TARGET)

$(TARGET) : $(OBJECTS)
	mkdir -p ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x86/
	$(CC) $(CCFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)
