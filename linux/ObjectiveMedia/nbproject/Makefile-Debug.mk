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
CND_PLATFORM=GNU-Linux-x86
CND_CONF=Debug
CND_DISTDIR=dist
CND_BUILDDIR=build

# Include project Makefile
include Makefile

# Object Directory
OBJECTDIR=${CND_BUILDDIR}/${CND_CONF}/${CND_PLATFORM}

# Object Files
OBJECTFILES= \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o \
	${OBJECTDIR}/platform/platform_codecs.o \
	${OBJECTDIR}/platform/platform_devices.o \
	${OBJECTDIR}/dbg.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o \
	${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o \
	${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o


# C Compiler Flags
CFLAGS=-m32

# CC Compiler Flags
CCFLAGS=-m32
CXXFLAGS=-m32

# Fortran Compiler Flags
FFLAGS=

# Assembler Flags
ASFLAGS=

# Link Libraries and Options
LDLIBSOPTIONS=-L/usr/lib/jvm/java-6-openjdk-amd64/lib -L../../../ffmpeg/build/x86/lib

# Build Targets
.build-conf: ${BUILD_SUBPROJECTS}
	"${MAKE}"  -f nbproject/Makefile-${CND_CONF}.mk ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libavcodec.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libavfilter.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libavformat.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libavutil.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libavdevice.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libswresample.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: libswscale.a

${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so: ${OBJECTFILES}
	${MKDIR} -p ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}
	${LINK.cc} -shared -o ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so -fPIC ${OBJECTFILES} ${LDLIBSOPTIONS} 

${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o: jni/com_mti_primitives_codecs_H263VideoEncoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoEncoder.o jni/com_mti_primitives_codecs_H263VideoEncoder.cpp

${OBJECTDIR}/platform/platform_codecs.o: platform/platform_codecs.cpp 
	${MKDIR} -p ${OBJECTDIR}/platform
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/platform/platform_codecs.o platform/platform_codecs.cpp

${OBJECTDIR}/platform/platform_devices.o: platform/platform_devices.cpp 
	${MKDIR} -p ${OBJECTDIR}/platform
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/platform/platform_devices.o platform/platform_devices.cpp

${OBJECTDIR}/dbg.o: dbg.cpp 
	${MKDIR} -p ${OBJECTDIR}
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/dbg.o dbg.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o: jni/com_mti_primitives_codecs_VC1VideoDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_VC1VideoDecoder.o jni/com_mti_primitives_codecs_VC1VideoDecoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o: jni/com_mti_primitives_devices_AudioInputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_devices_AudioInputDevice.o jni/com_mti_primitives_devices_AudioInputDevice.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o: jni/com_mti_primitives_codecs_G7231AudioDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioDecoder.o jni/com_mti_primitives_codecs_G7231AudioDecoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o: jni/com_mti_primitives_devices_VideoInputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoInputDevice.o jni/com_mti_primitives_devices_VideoInputDevice.cpp

${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o: jni/com_mti_primitives_devices_VideoOutputDevice.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_devices_VideoOutputDevice.o jni/com_mti_primitives_devices_VideoOutputDevice.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o: jni/com_mti_primitives_codecs_G7231AudioEncoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_G7231AudioEncoder.o jni/com_mti_primitives_codecs_G7231AudioEncoder.cpp

${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o: jni/com_mti_primitives_codecs_H263VideoDecoder.cpp 
	${MKDIR} -p ${OBJECTDIR}/jni
	${RM} $@.d
	$(COMPILE.cc) -g -I../../../ffmpeg/build/x86/include -I/usr/lib/jvm/java-6-openjdk-amd64/include/linux -I/usr/lib/jvm/java-6-openjdk-amd64/include -fPIC  -MMD -MP -MF $@.d -o ${OBJECTDIR}/jni/com_mti_primitives_codecs_H263VideoDecoder.o jni/com_mti_primitives_codecs_H263VideoDecoder.cpp

# Subprojects
.build-subprojects:

# Clean Targets
.clean-conf: ${CLEAN_SUBPROJECTS}
	${RM} -r ${CND_BUILDDIR}/${CND_CONF}
	${RM} ${CND_DISTDIR}/${CND_CONF}/${CND_PLATFORM}/libObjectiveMedia.so

# Subprojects
.clean-subprojects:

# Enable dependency checking
.dep.inc: .depcheck-impl

include .dep.inc
