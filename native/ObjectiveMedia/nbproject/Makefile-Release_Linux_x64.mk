#
# Generated Makefile - do not edit!
#
# Edit the Makefile in the project folder instead (../Makefile). Each target
# has a -pre and a -post target defined where you can add customized code.
#
# This makefile implements configuration specific macros and targets.


# Environment
MKDIR=mkdir
CP=cp
GREP=grep
NM=nm
CCADMIN=CCadmin
RANLIB=ranlib
CC=gcc
CCC=g++
CXX=g++
FC=gfortran
AS=as

# Macros
CND_PLATFORM=GNU-Linux
CND_DLIB_EXT=so
CND_CONF=Release_Linux_x64
CND_DISTDIR=dist
CND_BUILDDIR=build

# Include project Makefile
include Makefile

# Object Directory
OBJECTDIR=${CND_BUILDDIR}/${CND_CONF}/${CND_PLATFORM}

# Object Files
OBJECTFILES= \
	${OBJECTDIR}/dbg.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o \
	${OBJECTDIR}/platform/platform_codecs.o \
	${OBJECTDIR}/platform/platform_devices.o

# Test Directory
TESTDIR=${CND_BUILDDIR}/${CND_CONF}/${CND_PLATFORM}/tests

# Test Files
TESTFILES= \
	${TESTDIR}/TestFiles/f1

# Test Object Files
TESTOBJECTFILES= \
	${TESTDIR}/tests/testVideoInputDevice.o

# C Compiler Flags
CFLAGS=-m64

# CC Compiler Flags
CCFLAGS=-D__STDC_CONSTANT_MACROS
CXXFLAGS=-D__STDC_CONSTANT_MACROS

# Fortran Compiler Flags
FFLAGS=

# Assembler Flags
ASFLAGS=

# Link Libraries and Options
LDLIBSOPTIONS=-L../../ffmpeg/build/linux/x64/lib -L/usr/lib/jvm/java-8-oracle/lib/amd64 -L/usr/lib/jvm/java-8-oracle/lib -lswscale -lswresample -lavcodec -lavfilter -lavformat -lavutil -lavdevice

# Build Targets
.build-conf: ${BUILD_SUBPROJECTS}
	"${MAKE}"  -f nbproject/Makefile-${CND_CONF}.mk ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x64/objectivemedia_lin64.so

../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x64/objectivemedia_lin64.so: ${OBJECTFILES}
	${MKDIR} -p ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x64
	g++ -o ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x64/objectivemedia_lin64.so ${OBJECTFILES} ${LDLIBSOPTIONS} -Wl,-Bsymbolic -m64 -static-libstdc++ -shared -fPIC

${OBJECTDIR}/dbg.o: dbg.cpp 
	${MKDIR} -p ${OBJECTDIR}
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/dbg.o dbg.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o: jni/com_mti_primitives_codecs_G7231AudioDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o jni/com_mti_primitives_codecs_G7231AudioDecoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o: jni/com_mti_primitives_codecs_G7231AudioEncoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o jni/com_mti_primitives_codecs_G7231AudioEncoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o: jni/com_mti_primitives_codecs_H263VideoDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o jni/com_mti_primitives_codecs_H263VideoDecoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o: jni/com_mti_primitives_codecs_H263VideoEncoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o jni/com_mti_primitives_codecs_H263VideoEncoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o: jni/com_mti_primitives_codecs_VC1VideoDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o jni/com_mti_primitives_codecs_VC1VideoDecoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o: jni/com_mti_primitives_devices_AudioInputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o jni/com_mti_primitives_devices_AudioInputDevice.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice.o: jni/com_mti_primitives_devices_FileOutputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice.o jni/com_mti_primitives_devices_FileOutputDevice.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o: jni/com_mti_primitives_devices_VideoInputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o jni/com_mti_primitives_devices_VideoInputDevice.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o: jni/com_mti_primitives_devices_VideoOutputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o jni/com_mti_primitives_devices_VideoOutputDevice.cpp

${OBJECTDIR}/platform/platform_codecs.o: platform/platform_codecs.cpp 
	${MKDIR} -p ${OBJECTDIR}/platform
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/platform/platform_codecs.o platform/platform_codecs.cpp

${OBJECTDIR}/platform/platform_devices.o: platform/platform_devices.cpp 
	${MKDIR} -p ${OBJECTDIR}/platform
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/platform/platform_devices.o platform/platform_devices.cpp

# Subprojects
.build-subprojects:

# Build Test Targets
.build-tests-conf: .build-tests-subprojects .build-conf ${TESTFILES}
.build-tests-subprojects:

${TESTDIR}/TestFiles/f1: ${TESTDIR}/tests/testVideoInputDevice.o ${OBJECTFILES:%.o=%_nomain.o}
	${MKDIR} -p ${TESTDIR}/TestFiles
	${LINK.cc}   -o ${TESTDIR}/TestFiles/f1 $^ ${LDLIBSOPTIONS} -L../../../ffmpeg/build/x64/lib ../../../ffmpeg/build/x64/lib/libavcodec.a ../../../ffmpeg/build/x64/lib/libavdevice.a ../../../ffmpeg/build/x64/lib/libavfilter.a ../../../ffmpeg/build/x64/lib/libavformat.a ../../../ffmpeg/build/x64/lib/libavutil.a ../../../ffmpeg/build/x64/lib/libswresample.a ../../../ffmpeg/build/x64/lib/libswscale.a -lpthread 


${TESTDIR}/tests/testVideoInputDevice.o: tests/testVideoInputDevice.cpp 
	${MKDIR} -p ${TESTDIR}/tests
	${RM} "$@.d"
	$(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -I. -I. -I. -I. -I. -I. -I. -I. -I. -I. -I. -I. -MMD -MP -MF "$@.d" -o ${TESTDIR}/tests/testVideoInputDevice.o tests/testVideoInputDevice.cpp


${OBJECTDIR}/dbg_nomain.o: ${OBJECTDIR}/dbg.o dbg.cpp 
	${MKDIR} -p ${OBJECTDIR}
	@NMOUTPUT=`${NM} ${OBJECTDIR}/dbg.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/dbg_nomain.o dbg.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/dbg.o ${OBJECTDIR}/dbg_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o jni/com_mti_primitives_codecs_G7231AudioDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder_nomain.o jni/com_mti_primitives_codecs_G7231AudioDecoder.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o jni/com_mti_primitives_codecs_G7231AudioEncoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder_nomain.o jni/com_mti_primitives_codecs_G7231AudioEncoder.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o jni/com_mti_primitives_codecs_H263VideoDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder_nomain.o jni/com_mti_primitives_codecs_H263VideoDecoder.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o jni/com_mti_primitives_codecs_H263VideoEncoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder_nomain.o jni/com_mti_primitives_codecs_H263VideoEncoder.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o jni/com_mti_primitives_codecs_VC1VideoDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder_nomain.o jni/com_mti_primitives_codecs_VC1VideoDecoder.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o jni/com_mti_primitives_devices_AudioInputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice_nomain.o jni/com_mti_primitives_devices_AudioInputDevice.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice.o jni/com_mti_primitives_devices_FileOutputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice_nomain.o jni/com_mti_primitives_devices_FileOutputDevice.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice.o ${OBJECTDIR}/jni/com_mti_primitives_devices_FileOutputDevice_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o jni/com_mti_primitives_devices_VideoInputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice_nomain.o jni/com_mti_primitives_devices_VideoInputDevice.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice_nomain.o;\
	fi

${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice_nomain.o: ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o jni/com_mti_primitives_devices_VideoOutputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	@NMOUTPUT=`${NM} ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice_nomain.o jni/com_mti_primitives_devices_VideoOutputDevice.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice_nomain.o;\
	fi

${OBJECTDIR}/platform/platform_codecs_nomain.o: ${OBJECTDIR}/platform/platform_codecs.o platform/platform_codecs.cpp 
	${MKDIR} -p ${OBJECTDIR}/platform
	@NMOUTPUT=`${NM} ${OBJECTDIR}/platform/platform_codecs.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/platform/platform_codecs_nomain.o platform/platform_codecs.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/platform/platform_codecs.o ${OBJECTDIR}/platform/platform_codecs_nomain.o;\
	fi

${OBJECTDIR}/platform/platform_devices_nomain.o: ${OBJECTDIR}/platform/platform_devices.o platform/platform_devices.cpp 
	${MKDIR} -p ${OBJECTDIR}/platform
	@NMOUTPUT=`${NM} ${OBJECTDIR}/platform/platform_devices.o`; \
	if (echo "$$NMOUTPUT" | ${GREP} '|main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T main$$') || \
	   (echo "$$NMOUTPUT" | ${GREP} 'T _main$$'); \
	then  \
	    ${RM} "$@.d";\
	    $(COMPILE.cc) -g -s -I/usr/lib/jvm/java-8-oracle/include -I/usr/lib/jvm/java-8-oracle/include/linux -I../../ffmpeg/build/linux/x64/include -fPIC  -Dmain=__nomain -MMD -MP -MF "$@.d" -o ${OBJECTDIR}/platform/platform_devices_nomain.o platform/platform_devices.cpp;\
	else  \
	    ${CP} ${OBJECTDIR}/platform/platform_devices.o ${OBJECTDIR}/platform/platform_devices_nomain.o;\
	fi

# Run Test Targets
.test-conf:
	@if [ "${TEST}" = "" ]; \
	then  \
	    ${TESTDIR}/TestFiles/f1 || true; \
	else  \
	    ./${TEST} || true; \
	fi

# Clean Targets
.clean-conf: ${CLEAN_SUBPROJECTS}
	${RM} -r ${CND_BUILDDIR}/${CND_CONF}
	${RM} ../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/lin/x64/objectivemedia_lin64.so

# Subprojects
.clean-subprojects:

# Enable dependency checking
.dep.inc: .depcheck-impl

include .dep.inc
