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
#include "platform_devices.h"
#include <stdio.h>
/********************************************
Linux Specific Structures and functions
********************************************/


typedef struct VideoInputDeviceContext{
	
}VideoDeviceContext;

typedef struct AudioInputDeviceContext{
	
}AudioInputDeviceContext;

typedef struct VideoOutputDeviceContext{
	
}VideoOutputDeviceContext;

typedef struct AudioOutputDeviceContext{
	
}AudioOutputDeviceContext;



/********************************************
VideoMediaFormat Implementation
********************************************/
VideoMediaFormat::VideoMediaFormat(){

}

VideoMediaFormat::~VideoMediaFormat(){

}

/********************************************
AudioMediaFormat Implementation
********************************************/
AudioMediaFormat::AudioMediaFormat(){

}

AudioMediaFormat::~AudioMediaFormat(){

}

/********************************************
VideoInputDevice Implementation
********************************************/
VideoInputDevice::VideoInputDevice(){
	this->DeviceName = "";
	this->DeviceIndex = 0;
	this->Listener = NULL;
	this->DeviceContext = NULL;
	FormatCount = 0;
}

Device_Errors VideoInputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try
	{
		Close();
		VideoInputDeviceContext* context = new VideoInputDeviceContext();
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors VideoInputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try
	{
		if(DeviceContext != NULL)
		{
			VideoInputDeviceContext* context = (VideoInputDeviceContext*)DeviceContext;
			
		}
		SAFEDELETE(DeviceContext);
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors VideoInputDevice::GetDevices(std::vector<Device*> &deviceList){
	Device_Errors retval = SUCCEEDED;
	//CoInitialize(NULL);
	try
	{
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

VideoInputDevice::~VideoInputDevice(){
	Close();
	for(int x=0; x < FormatCount; x++)
	{
		if(Formats[x] != NULL)
		{
				delete(Formats[x]);
				Formats[x] = NULL;
		}
	}
	Formats.clear();
}

/********************************************
AudioInputDevice Implementation
*********************************************/

AudioInputDevice::AudioInputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
}

Device_Errors AudioInputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try
	{
		Close();
		AudioInputDeviceContext* context = new AudioInputDeviceContext();
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors AudioInputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try
	{
		if(DeviceContext != NULL)
		{
			AudioInputDeviceContext* context = (AudioInputDeviceContext*)DeviceContext;
			
			
		}
		SAFEDELETE(DeviceContext);
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors AudioInputDevice::GetDevices(std::vector<Device*> &deviceList){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

AudioInputDevice::~AudioInputDevice()
{
	Close();
	for(int x=0; x < FormatCount; x++)
	{
		if(Formats[x] != NULL)
		{
				delete(Formats[x]);
				Formats[x] = NULL;
		}
	}
	Formats.clear();
};

/********************************************
VideoOutputDevice Implementation
********************************************/
VideoOutputDevice::VideoOutputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
	//See OutputDevice header.
Device_Errors VideoOutputDevice::Present(void* sample, long size, long long timestamp){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device Header.
Device_Errors VideoOutputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}
	//Opens the output device with a specified surface, width, height and rotation.
Device_Errors VideoOutputDevice::Open(MediaFormat* format, void* surface, int width, int height, bool rotate){
	Device_Errors retval = SUCCEEDED;
	try
	{
		Surface = surface;
		SurfaceWidth = width;
		SurfaceHeight = height;
		RotateFrames = rotate;
		Open(format);
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}

	//See Device Header
Device_Errors VideoOutputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device Header
Device_Errors VideoOutputDevice::GetDevices(std::vector<Device*> &deviceList){
	return NOT_SUPPORTED;
}

VideoOutputDevice::~VideoOutputDevice(){
	Close();
}

/*********************************************
AudioOutputDevice Implementation
*********************************************/
AudioOutputDevice::AudioOutputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
	//See OutputDevice header.
Device_Errors AudioOutputDevice::Present(void* sample, long size, long long timestamp){
	Device_Errors retval = SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)DeviceContext;
		if(DeviceContext == NULL){
			retval = INVALID_DEVICE;
		}
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = new AudioOutputDeviceContext();
		AudioMediaFormat* aformat = (AudioMediaFormat*)format;
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)DeviceContext;
		
		SAFEDELETE(DeviceContext);
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::GetDevices(std::vector<Device*> &deviceList){
	Device_Errors retval = SUCCEEDED;
	try{
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

AudioOutputDevice::~AudioOutputDevice(){
	Close();
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
