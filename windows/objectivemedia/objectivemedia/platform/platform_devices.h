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
File: platform_devices.h
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Create Date: 6/13/2012
Description: The Platform Devices header file provides definitions of all platform
specific media device interfaces.

Revision History:
0.1 - 6/13/2012 - Initial Creation
0.2 - 6/21/2012 - Changed "Formats" in device class to be of type "vector<MediaFormat*>
	and changed the "devList" parameter in "GetDevices" to be "vector<Device*>"
***************************************************************************************/

#include "platform_includes.h"
extern "C"{
	#include <libavutil/imgutils.h>
	#include <libavutil/opt.h>
	#include <libavcodec/avcodec.h>
	#include <libavutil/mathematics.h>
	#include <libavutil/samplefmt.h>
}

using namespace std;

#ifndef DEVICE_DEFS
#define DEVICE_DEFS
#endif


/**************************************************************************************
Description: The DeviceListener class serves as a base class for any user class that
would receive a callback from a device implementation once it has captured a sample or
chunk of samples.
***************************************************************************************/
class DeviceListener{
public:
	/*The SampleCaptured function is implemented by the inheriting class to receive samples from
	a device. The "sender" parameter is a pointer to the calling device. This will always be an
	object that inherits "Device". The "sample" parameter is a pointer to the data captured by
	the device. The "size" parameter provides the size of the sample, in bytes. The "timestamp"
	parameter designates the timestamp (hardware and platform specific) at which the sample was
	captured.
	*/
	virtual void SampleCaptured(void* sender, void* sample, long size, long long timestamp) = 0;
};

/**************************************************************************************
Description: The Device class provides basic definition for all device implementations.
All other device implementations are a child of this class.
***************************************************************************************/
class Device{
public:
	string DeviceName; //The name of the device.
	int DeviceIndex; //The 0-based index of the device in the list of devices.
	vector <MediaFormat*> Formats; //An array of MediaFormats that are supported by this device.
	int FormatCount; //The number of formats in the Formats array.
	DeviceListener* Listener; //A pointer to a Listener object that will receive callbacks.
	void* DeviceContext;
public:
	/*The Open function opens the device for use. If it is an input device, then this begins the
	capture process. If it's an output device, then this allocates all necessary resources to 
	perform the presentation of the media.*/
	virtual Device_Errors Open(MediaFormat* format) = 0;
	/*The Close function closes the device and deallocates all resources used by the device.*/
	virtual Device_Errors Close() = 0;
	/*The GetDevices function provides an array of Devices available on the machine.*/
	virtual Device_Errors GetDevices(vector<Device*> &devList) = 0;
	/*The ToString function represents the object as a string, typically by returning the name*/
	virtual string ToString(){
		return DeviceName;	
	};
	static void FreeBuffer(void* buffer){
		av_free(buffer);
	};
	static void* AllocBuffer(int size)
	{
		return av_malloc(size);
	};
protected:
};

/**************************************************************************************
Description: The VideoMediaFormat class defines the format for video media on this platform.
***************************************************************************************/
class VideoMediaFormat:public MediaFormat{
public:
	int VideoType; //A platform specific designation
	int Width; //The width, in pixels, of the video.
	int Height; //the height, in pixels, of the video.
	int FPS; //the Frames-Per-Second for the video.
	VideoPixelFormat PixelFormat; //The pixel format of the video.

	VideoMediaFormat();
	~VideoMediaFormat();
	/*The GetPixelBits provides the pixel width (in bits) of the provided format.*/
	static int GetPixelBits(VideoPixelFormat format){
		int retval = 0;
		switch(format){
		case RGB1: //1 bit
			retval = 1;
			break;
		case RGB4: //4 bit
			retval = 4;
			break;
		case RGB8: //8 bit
			retval = 8;
			break;
		case RGB555: //15 bit
			retval = 16;
			break;
		case RGB565: //16 bit
			retval = 16;
			break;
		case RGB24: //24 bit
			retval = 24;
			break;
		case RGB32: //32 bit
			retval = 32;
			break;
		case ARGB32: //32 bit
			retval = 32;
			break;
		case AYUV: //32 bit
			retval = 32;
			break;
		case UYVY: //16 bit
			retval = 16;
			break;
		case Y411: //12 bit
			retval = 12;
			break;
		case Y41P: //12 bit
			retval = 12;
			break;
		case Y211: //8 bit
			retval = 8;
			break;
		case YUY2: //16 bit
			retval = 1;
			break;
		case YVYU: //16 bit
			retval = 16;
			break;
		case YUYV: //16 bit
			retval = 16;
			break;
		case IF09: //9.5 bits
			retval = 9;
			break;
		case IYUV: //12 bits
			retval = 12;
			break;
		case YV12: //12 bits
			retval = 12;
			break;
		case YVU9: //9 buts
			retval = 9;
			break;
		case I420: //12 bits
			retval = 12;
			break;
		case UNKNOWN: //unknown pixel size.
			retval = 0;
			break;
		case ANY: //any pixel size.
			retval = 0;
			break;
		}
		return retval;
	};

	static int GetFFPixel(VideoPixelFormat format){
		int retval = 0;
		switch(format){
		case RGB1: //1 bit
			retval = PIX_FMT_MONOBLACK;
			break;
		case RGB4: //4 bit
			retval = PIX_FMT_RGB4;
			break;
		case RGB8: //8 bit
			retval = PIX_FMT_RGB8;
			break;
		case RGB555: //15 bit
			retval = PIX_FMT_RGB555LE;
			break;
		case RGB565: //16 bit
			retval = PIX_FMT_RGB565LE;
			break;
		case RGB24: //24 bit
			retval = PIX_FMT_BGR24;
			break;
		case RGB32: //32 bit
			retval = PIX_FMT_BGR0;
			break;
		case ARGB32: //32 bit
			retval = PIX_FMT_BGRA;
			break;
		case AYUV: //32 bit
			retval = PIX_FMT_YUVA444P;
			break;
		case UYVY: //16 bit
			retval = PIX_FMT_UYVY422;
			break;
		case Y411: //12 bit
			retval = PIX_FMT_UYYVYY411;
			break;
		case Y41P: //12 bit
			retval = PIX_FMT_YUV411P;
			break;
		case Y211: //8 bit
			retval = PIX_FMT_YUV410P;
			break;
		case YUY2: //16 bit
			retval = PIX_FMT_UYVY422;
			break;
		case YVYU: //16 bit
			retval = PIX_FMT_UYVY422;
			break;
		case YUYV: //16 bit
			retval = PIX_FMT_UYVY422;
			break;
		case IF09: //9.5 bits
			retval = PIX_FMT_YUV410P;
			break;
		case IYUV: //12 bits
			retval = PIX_FMT_YUV420P;
			break;
		case YV12: //12 bits
			retval = PIX_FMT_YUV420P;
			break;
		case YVU9: //9 bits
			retval = PIX_FMT_YUV410P;
			break;
		case I420: //12 bits
			retval = PIX_FMT_YUV420P;
			break;
		case UNKNOWN: //unknown pixel size.
			retval = 0;
			break;
		case ANY: //any pixel size.
			retval = 0;
			break;
		}
		return retval;
	};
protected:
	
};

/**************************************************************************************
Description: The AudioMediaFormat class defines the format for PCM audio on this platform.
***************************************************************************************/
class AudioMediaFormat:public MediaFormat{
public:
	int SampleRate; //The sample rate at which the audio should be captured.
	int BitsPerSample; //The number of bits per sample.
	int Channels; //The number of channels to capture.

	AudioMediaFormat();
	~AudioMediaFormat();
protected:
	
};

/**************************************************************************************
Description: The InputDevice class serves as an inheritance marker for all input devices.
***************************************************************************************/
class InputDevice: public Device{

};

/**************************************************************************************
Description: The OutputDevice serves as an inheritance marker for all output devices.
***************************************************************************************/
class OutputDevice: public Device{
public:
	/*The Present function receives a sample and a timestamp that it then presents through the
	output hardware for the device. The "sample" parameter is a pointer to a byte array that
	represents the media sample. The "size" parameter describes the size of the sample array.
	The "timestamp" parameter provides a platform specific time reference at which the sample
	was acquired.*/
	virtual Device_Errors Present(void* sample, long size, long long timestamp) = 0;
};

/**************************************************************************************
Description: The VideoInputDevice class provides functionality for interfacing to hardware
that provides video input.
***************************************************************************************/
class VideoInputDevice: public InputDevice{
public:
	VideoInputDevice();
	//see Device header.
	Device_Errors Open(MediaFormat* format);
	//see Device header.
	Device_Errors Close();
	//see Device header.
	Device_Errors GetDevices(vector<Device*> &deviceList);
	~VideoInputDevice();
protected:
	
};

/**************************************************************************************
Description: The AudioInputDevice class provides functionality for interfacing to hardware
that provides audio input.
***************************************************************************************/
class AudioInputDevice : public InputDevice{
public:
	AudioInputDevice();
	//See Device header.
	virtual Device_Errors Open(MediaFormat* format);
	//See Device header.
	virtual Device_Errors Close();
	//See Device header.
	virtual Device_Errors GetDevices(vector<Device*> &deviceList);
	~AudioInputDevice();
protected:
	
};

/**************************************************************************************
Description: The VideoOutputDevice class provides functionality for outputting video to
a hardware device.
***************************************************************************************/
class VideoOutputDevice: public OutputDevice{
public:
	void* Surface; //a pointer to a surface (Memory Bitmap or Window) onto which the video should be drawn.
	int SurfaceWidth; //The width of the surface.
	int SurfaceHeight; //The height of the surface.
	bool RotateFrames; //Should the class rotate each frame before displaying it? True=Yes, False=No.

	VideoOutputDevice();
	//See OutputDevice header.
	virtual Device_Errors Present(void* sample, long size, long long timestamp);
	//See Device Header.
	virtual Device_Errors Open(MediaFormat* format);
	//Opens the output device with a specified surface, width, height and rotation.
	Device_Errors Open(MediaFormat* format, void* surface, int width, int height, bool rotate);
	//See Device Header
	virtual Device_Errors Close();
	//See Device Header
	virtual Device_Errors GetDevices(vector<Device*> &deviceList);

	~VideoOutputDevice();
protected:
	//Pointer to the current format used to open the device.
	VideoMediaFormat* CurrentFormat;
	
};

/**************************************************************************************
Description: The AudioOutputDevice class provides functionality for outputting audio to
a hardware device.
***************************************************************************************/
class AudioOutputDevice: public OutputDevice{
public:
	AudioOutputDevice();
	//See OutputDevice header.
	virtual Device_Errors Present(void* sample, long size, long long timestamp);
	//See Device header.
	virtual Device_Errors Open(MediaFormat* format);
	//See Device header.
	virtual Device_Errors Close();
	//See Device header.
	virtual Device_Errors GetDevices(vector<Device*> &deviceList);
	~AudioOutputDevice();
protected:
	AudioMediaFormat* CurrentFormat;
};