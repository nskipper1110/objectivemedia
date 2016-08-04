SHELL = /bin/sh
CC    = gcc
CCFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
CFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
CXXFLAGS = -D__STDC_CONSTANT_MACROS
LDFLAGS      = -shared -L/usr/lib/jvm/java-8-oracle/lib \
					   -L/usr/lib/jvm/java-8-oracle/lib/amd64 \
					   -L../../ffmpeg/build/linux/x86/lib \
					   -lswscale \
					   -lswresample \
					   -lavcodec \
					   -lavfilter \
					   -lavformat \
					   -lavutil \
					   -lavdevice \
					   -lgcc \
                       -lstdc++
INCLUDES = -I/usr/lib/jvm/java-8-oracle/include \
		   -I/usr/lib/jvm/java-8-oracle/include/linux \
		   -I../../ffmpeg/build/linux/x86/include \
		   -I. \
		   -I./jni \
		   -I./platform

TARGET  = ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x86/objectivemedia_lin32.dll
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
	mkdir -p ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x86/
	$(CC) $(CCFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)
