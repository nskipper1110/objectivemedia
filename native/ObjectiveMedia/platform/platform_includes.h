/*
 * copyright (c) 2013 Nathan Skipper, Montgomery Technology, Inc.
 *
 * This file is part of ObjectiveMedia (http://nskipper1110.github.com/objectivemedia).
 *
 * ObjectiveMedia is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * ObjectiveMedia is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with ObjectiveMedia; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
/***************************************************************************************
File: platform_includes.h
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Create Date: 6/13/2012
Description: The Platform Includes header file provides a single point of inlcusion for
standard system header files for the platform specific classes.

Revision History:
0.1 - 6/13/2012 - Initial Creation

***************************************************************************************/
#pragma once
#include "../dbg.h"
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string>
#include <cstring>
#include <vector>

#define   SAFERELEASE(x)            if((x)){ (x)->Release(); (x) = NULL;}
#define   SAFEDELETE(x)             if((x)){ delete [] (x);  (x) = NULL;}
#define   SAFEDELETES(x)            if((x)){ delete    (x);  (x) = NULL;}
#define   SAFEFREE(x)               if((x)){ free(x);        (x) = NULL;}

/**************************************************************************************
Description: The Device_Error enumerator provides a list of possible errors that might
be experienced when calling a function within this namespace.
***************************************************************************************/

typedef enum Device_Errors{
	SUCCEEDED=0, //call to the function was successful.
	NO_DEVICES=1, //there are no devices available
	INVALID_DEVICE=2, //the device provided or used is not valid.
	INVALID_DATA=3, //the data provided or used is not valid.
	NO_INPUT=4, //there is no input device available.
	NO_OUTPUT=5, //there is no output available.
	INVALID_FORMAT=6, //The format provided is invalid for this device.
	NO_FORMATS=7, //There are no formats for this device.
	NOT_SUPPORTED=8, //The function is not supported for this device.
	UNEXPECTED=9 //There was an unexpected error within the function call.
}Device_Errors;

/**************************************************************************************
Description: The VideoPixelFormat provides the enumeration of supported video pixel
formats. Note that not all formats are supported by all devices or all platforms.
Check for the INVALID_FORMAT error to validate pixel formats.
***************************************************************************************/
typedef enum VideoPixelFormat{
	RGB1=	1, //1 bit
	RGB4=	4, //4 bit
	RGB8=	8, //8 bit
	RGB555=	15, //15 bit
	RGB565=	16, //16 bit
	RGB24=	24, //24 bit
	RGB32=	31, //32 bit
	ARGB32=	32, //32 bit
	AYUV=	65, //32 bit
	UYVY=	66, //16 bit
	Y411=	67, //12 bit
	Y41P=	68, //12 bit
	Y211=	69, //8 bit
	YUY2=	70, //16 bit
	YVYU=	71, //16 bit
	YUYV=	72, //16 bit
	IF09=	73, //9.5 bits
	IYUV=	74, //12 bits
	YV12=	75, //12 bits
	YVU9=	76, //9 buts
	I420=	77, //12 bits
        NV21=   78, //12 bits
	UNKNOWN=99, //unknown pixel size.
	ANY=	0, //any pixel size.
}VideoPixelFormat;

/**************************************************************************************
Description: The MediaFormat class provides serves as a base class for any media format
within a device in this namespace.
***************************************************************************************/
class MediaFormat{
public:
};

static void avlog_cb(void * ptr, int level, const char * szFmt, va_list varg) {
    char* mymsg = new char[strlen(szFmt) + 250];
    //va_start(varg);
    
    vsprintf(mymsg, szFmt, varg);
    va_end(varg);
    sprintf(dbg_buffer, "FFMPEG: ");
    DbgOut(dbg_buffer);
    sprintf((char*)dbg_buffer, "%s", (const char*)mymsg);
    DbgOut(dbg_buffer);
    //sprintf(dbg_buffer, "*****STOP FFMPEG LOG ENTRY*****\n");
    //DbgOut(dbg_buffer);
}


