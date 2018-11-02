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
#include "com_mti_primitives_devices.h"
using namespace std;
static VideoInputDevice* videoInputDevice = NULL;
static JavaVM* CallbackJVM = NULL;
static jobject MyListener = NULL;
static jobject jvideoInputDevice = NULL;

class VideoInputDeviceListener : public DeviceListener
{
	void SampleCaptured(void* sender, void* sample, long size, long long timestamp)
	{
		//DebugOut("VideoInputDeviceListener.SampleCaptured++\n");
		if(MyListener != NULL && CallbackJVM != NULL && sample != NULL && size > 0)
		{
			//DebugOut("Listener and JVM are instantiated.\n");
			JNIEnv* CallbackEnv = NULL;
			//DebugOut("Attaching to current thread.\n");
                        int jvmRet = 0;
#ifdef __ANDROID__
                        jvmRet = (*CallbackJVM).AttachCurrentThread(&CallbackEnv, NULL);
#else
                        jvmRet = CallbackJVM->AttachCurrentThread((void**)&CallbackEnv, NULL);
#endif
			if(jvmRet == 0)
			{
				//DebugOut("Creating new byte array\n");
				jbyteArray frame = CallbackEnv->NewByteArray(size);
				if(frame != NULL)
				{
					//DebugOut("Setting frame to values of buffer.\n");
					CallbackEnv->SetByteArrayRegion(frame, 0,size, (jbyte*) sample);
					jlong tstamp = timestamp;
					//DebugOut("Getting Listener class\n");
					jclass cls = CallbackEnv->GetObjectClass(MyListener);
					if(cls != NULL){
						//DebugOut("Getting listener SampleCaptured function id\n");
						jmethodID id = CallbackEnv->GetMethodID(cls, "SampleCaptured", "(Lcom/mti/primitives/devices/Device;[BJ)V");
						if(id != NULL){
							//char buffer[1000];
							//sprintf(buffer, "Calling SampleCaptured with video size of %d", size);
							//DebugOut(buffer);
							CallbackEnv->CallVoidMethod(MyListener, id, jvideoInputDevice, frame, tstamp);
						}
					}
				}
				//DebugOut("Detaching thread\n");
#ifndef __ANDROID__
				CallbackJVM->DetachCurrentThread();
#else
                                (*CallbackJVM).DetachCurrentThread();
#endif
			}
		
		}
		//DebugOut("VideoInputDeviceListener.SampleCaptured--");
	}
};



JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoInputDevice_PlatformOpen
  (JNIEnv * Env, jobject sender, jobject listener, jint width, jint height, jint pixelFormat, jint fps){
	  jint retval = 0;
	  try{
		  if(Env->GetJavaVM(&CallbackJVM) != 0)
		  {
			  retval = (jint)NOT_SUPPORTED;
		  }
		  else if(listener == NULL){
			  retval = (jint)INVALID_DATA;
		  }
		  else{
			  MyListener = Env->NewGlobalRef(listener);
			  jvideoInputDevice = Env->NewGlobalRef(sender);
			  //VideoInputDevice* tempDevice = new VideoInputDevice();
                          videoInputDevice = new VideoInputDevice();
			  Java_To_VideoInputDevice(Env, sender, videoInputDevice);
//			  vector<Device*> deviceList;
//			  if(tempDevice->GetDevices(deviceList) == SUCCEEDED){
//				  for(int x = 0; x < deviceList.size(); x++)
//				  {
//					  if(((VideoInputDevice*)deviceList[x])->DeviceIndex != tempDevice->DeviceIndex)
//						  delete deviceList[x];
//                                          else
//                                          {
//                                              videoInputDevice = (VideoInputDevice*)deviceList[x];
//                                          }
//				  }
//				  deviceList.clear();
				  VideoInputDeviceListener* clistener = new VideoInputDeviceListener();
				  videoInputDevice->Listener = clistener;
				  VideoMediaFormat* format = new VideoMediaFormat();
				  format->Width = width;
				  format->Height = height;
				  format->FPS = fps;
				  format->PixelFormat = (VideoPixelFormat) pixelFormat;
				  char buffer[1000];
				  sprintf(dbg_buffer,"Opening device index %d, device name %s, format width %d, height %d, fps %d, Pixel format %d\n", videoInputDevice->DeviceIndex, videoInputDevice->DeviceName.c_str(), format->Width, format->Height, format->FPS, format->PixelFormat);
				  DbgOut(dbg_buffer);
				  retval = (jint)videoInputDevice->Open(format);
				  sprintf(dbg_buffer, "Open returned %d\n", retval);
				  DbgOut(dbg_buffer);
//			  }
//			  else{
//				  retval = (jint)NO_DEVICES;
//			  }
			  
		  }
	  }
	  catch(...){
		  retval = (jint)UNEXPECTED;
	  }
	  return retval;
}

/*
 * Class:     com_mti_primitives_devices_VideoInputDevice
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoInputDevice_PlatformClose
  (JNIEnv * Env, jobject sender){
	  jint retval = 0;
	  if(videoInputDevice != NULL)
	  {
		  retval = (jint)videoInputDevice->Close();
		  delete videoInputDevice;
		  videoInputDevice = NULL;
	  }
	  return retval;
}

/*
 * Class:     com_mti_primitives_devices_VideoInputDevice
 * Method:    PlatformGetDevices
 * Signature: ([Lcom/mti/primitives/devices/VideoInputDevice;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoInputDevice_PlatformGetDevices
  (JNIEnv * Env, jobject sender, jobjectArray deviceList){
	  Device_Errors retval = SUCCEEDED;

	  VideoInputDevice* vd = new VideoInputDevice();
	  std::vector<Device*> devList;
	  retval = vd->GetDevices(devList);
	  if(retval == SUCCEEDED)
	  {
		  int size = Env->GetArrayLength(deviceList);
		  for(int x = 0; x < size; x++)
		  {
			  if(x < devList.size()){
				  jobject dev = New_jVideoInputDevice(Env, (VideoInputDevice*) devList[x]);
				  delete(devList[x]);
				  Env->SetObjectArrayElement(deviceList, x, dev);
			  }
			  else{
				  Env->SetObjectArrayElement(deviceList, x, NULL);
			  }
		  }
		  devList.clear();
	  }

	  return retval;
}
