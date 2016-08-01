SHELL = /bin/sh
<<<<<<< HEAD
CC    = gcc -v
=======
CC    = gcc
>>>>>>> ce0552a01e9649381e1ea4cc97af4623fc30dc78
CCFLAGS = -m64 -fPIC -D__STDC_CONSTANT_MACROS -fpermissive
CFLAGS = -m64 -fPIC -D__STDC_CONSTANT_MACROS -fpermissive
CXXFLAGS = -D__STDC_CONSTANT_MACROS -fpermissive
LDFLAGS      = -shared \
					   -L/c/jdk/lib \
					   -L/c/jdk/lib/amd64 \
					   -L../../ffmpeg/build/win/x64/lib \
<<<<<<< HEAD
					   -L"/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/i686-w64-mingw32/lib" \
=======
>>>>>>> ce0552a01e9649381e1ea4cc97af4623fc30dc78
					   -lswscale \
					   -lswresample \
					   -lavcodec \
					   -lavfilter \
					   -lavformat \
					   -lavutil \
					   -lavdevice \
					   -lgcc \
					   -liconv \
<<<<<<< HEAD
					   -pthread \
					   -lstdc++
INCLUDES = -I/c/jdk/include \
		   -I/c/jdk/include/win32 \
		   -I../../ffmpeg/build/win/x64/include \
		   -I"/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/i686-w64-mingw32/include" \
=======
					   -lstdc++ \
					   -lquartz \
					   -lstrmiids \
					   -lole32 \
					   -luuid
INCLUDES = -I/c/jdk/include \
		   -I/c/jdk/include/win32 \
		   -I../../ffmpeg/build/win/x64/include \
>>>>>>> ce0552a01e9649381e1ea4cc97af4623fc30dc78
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
