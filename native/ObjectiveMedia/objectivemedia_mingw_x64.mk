SHELL = /bin/sh
CC    = gcc
CCFLAGS = -m64 -fPIC -D__STDC_CONSTANT_MACROS -fpermissive
CFLAGS = -m64 -fPIC -D__STDC_CONSTANT_MACROS -fpermissive
CXXFLAGS = -D__STDC_CONSTANT_MACROS -fpermissive
LDFLAGS      = -shared \
					   -L/c/jdk/lib \
					   -L/c/jdk/lib/amd64 \
					   -L../../ffmpeg/build/win/x64/lib \
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
		   -I../../ffmpeg/build/win/x64/include \
		   -I. \
		   -I./jni \
		   -I./platform

TARGET  = ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x64/objectivemedia_win64.dll
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
	mkdir -p ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x64/
	$(CC) $(CCFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)
