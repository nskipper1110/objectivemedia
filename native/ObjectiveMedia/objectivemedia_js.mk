SHELL = /bin/sh
CC    = emcc
CCFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
CFLAGS = -m32 -fPIC -D__STDC_CONSTANT_MACROS
CXXFLAGS = -D__STDC_CONSTANT_MACROS -D__JS__
LDFLAGS      = 		   -L../../ffmpeg/build/linux/x86/lib \
					   -lswscale \
					   -lswresample \
					   -lavcodec \
					   -lavfilter \
					   -lavformat \
					   -lavutil \
					   -lavdevice \
					   -lgcc \
                       -lstdc++
INCLUDES = -I../../ffmpeg/build/linux/x86/include \
		   -I. \
		   -I./platform

TARGET  = ./objectivemedia.bc
SOURCES = $(shell echo ./*.cpp) \
		  $(shell echo ./platform/*.cpp) \
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
	mkdir -p ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/js/x86/
	$(CC) $(CCFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)
