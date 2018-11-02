SHELL = /bin/sh
CC    = emcc
CXX   = em++
CCFLAGS = -O3 -s ALLOW_MEMORY_GROWTH=1 -s ASSERTIONS=2 -s OUTLINING_LIMIT=100000 -s TOTAL_MEMORY=134217728  -s DISABLE_EXCEPTION_CATCHING=0  --memory-init-file 1 -s ERROR_ON_UNDEFINED_SYMBOLS=0
CFLAGS = -O3 -s ALLOW_MEMORY_GROWTH=1 -s ASSERTIONS=2 -s OUTLINING_LIMIT=100000 -s TOTAL_MEMORY=134217728  -s DISABLE_EXCEPTION_CATCHING=0  --memory-init-file 1 -D__JS__ -s ERROR_ON_UNDEFINED_SYMBOLS=0
CXXFLAGS = -O3 -s ALLOW_MEMORY_GROWTH=1 -s ASSERTIONS=2 -s OUTLINING_LIMIT=100000 -s TOTAL_MEMORY=134217728  -s DISABLE_EXCEPTION_CATCHING=0  --memory-init-file 1 -D__JS__ -std=c++11 -s ERROR_ON_UNDEFINED_SYMBOLS=0
LDFLAGS      = 		   -L../../ffmpeg/build/js/x86/lib \
					   -lswscale \
					   -lswresample \
					   -lavcodec \
					   -lavfilter \
					   -lavformat \
					   -lavutil \
					   -lavdevice
INCLUDES = -I../../ffmpeg/build/js/x86/include \
		   -I. \
		   -I./platform

TARGET  = ./build/js/x86/objectivemedia.js
SOURCES = $(shell echo ./*.cpp) \
		  $(shell echo ./platform/*.cpp) \
		  $(shell echo ./js/*.cpp) \
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
	mkdir -p build/js/x86/
	$(CC) $(CCFLAGS) $(OBJECTS) -o $@ $(LDFLAGS)
