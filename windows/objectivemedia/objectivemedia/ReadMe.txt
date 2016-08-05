========================================================================
    DYNAMIC LINK LIBRARY : objectivemedia Project Overview
========================================================================

The ObjectiveMedia project is a library aimed at providing an object oriented approach to multimedia programming,
with cross platform functionality and support for OO languages like Java as it's primary goals. The source code
provided in this project represents the Microsoft Windows implementation of this library.

All code provided under this project is provided under the GNU Lesser General Public License (LGPL) v 2.1. Copyright(C)
is reserved by Nathan Skipper and Montgomery Technology, Inc.

This project makes use of the FFMPEG project. More information about FFMPEG can be found at www.ffmpeg.org. The source code
and scripts used to compile FFMPEG can be found under the ./FFMPEG folder on this repository.

Dependencies:
This project is dependent on static libraries from FFMPEG (compiled separately) and Java JDK JNI. This project is configured
to assume that FFMPEG includes and libraries are located under "C:\ffmpeg\build\x86" or "C:\ffmpeg\build\x64", depending
on the selected build configuration. JDK dependencies are assumed to be under "C:\program files\java\jdk...".

This project seeks to make use of MinGW static libraries and includes where possible instead of Microsoft SDK includes. This
is done to minimize platform dependencies.

Structure:
The project code is broken down into three major categories: platform, jni, and api (yet to come). Code under "platform" provides
functionality for accessing media devices specific to the OS/Arch used. Code in this category should remain as generic as possible, until specific
OS features must be accessed.

Code under "jni" should provide functionality for relating the platform code to Java Native Interface.

Code under "api" should provide functionality for relating the platform code to Win32 DLL access.
