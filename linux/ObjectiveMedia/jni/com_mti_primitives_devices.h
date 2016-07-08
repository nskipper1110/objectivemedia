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

#include "com_mti_primitives_devices_VideoInputDevice.h"
#include "com_mti_primitives_devices_FileOutputDevice.h"
#include "../platform/platform_devices.h"

static jobject New_jVideoMediaFormat(JNIEnv* Env, VideoMediaFormat* cformat){
	jobject format = NULL;
	if(Env != NULL && cformat != NULL){
		jclass cls = Env->FindClass("com/mti/primitives/devices/VideoMediaFormat");
		if(cls != NULL){
			jmethodID constructor = Env->GetMethodID(cls, "<init>", "(IIILcom/mti/primitives/devices/VideoPixelFormat;)V");
			if(constructor != NULL){
				jclass pixelcls = Env->FindClass("com/mti/primitives/devices/VideoPixelFormat");
				if(pixelcls != NULL)
				{
					
					jmethodID nativeid = Env->GetStaticMethodID(pixelcls, "FromNative", "(I)Lcom/mti/primitives/devices/VideoPixelFormat;");
					if(nativeid != NULL){
						jobject pixelFormat = Env->CallStaticObjectMethod(pixelcls, nativeid, (int)cformat->PixelFormat);
						if(pixelFormat != NULL){
							format = Env->NewObject(cls, constructor, cformat->FPS, cformat->Width, cformat->Height, pixelFormat);
						}
					}
				}
			}
		}
	}

	return format;
}

static void Add_jVideoMediaFormat_To_jVideoInputDevice(JNIEnv* Env, jobject jinputDevice, VideoMediaFormat* cformat){
	if(Env != NULL && jinputDevice != NULL && cformat != NULL){
		jclass cls = Env->GetObjectClass(jinputDevice);
		if(cls != NULL){
			jfieldID formatsID = Env->GetFieldID(cls, "Formats", "Ljava/util/List;");
			if(formatsID != NULL){
				jobject formats = Env->GetObjectField(jinputDevice, formatsID);
				if(formats != NULL){
					jclass formatscls = Env->GetObjectClass(formats);
					if(formatscls != NULL){
						jmethodID addmethod = Env->GetMethodID(formatscls, "add", "(Ljava/lang/Object;)Z");
						if(addmethod != NULL){
							jobject jformat = New_jVideoMediaFormat(Env, cformat);
							if(jformat != NULL){
								Env->CallBooleanMethod(formats, addmethod, jformat);
							}
						}
					}	
				}
			}
		}
		
	}
}

static jobject New_jAudioMediaFormat(JNIEnv* Env, AudioMediaFormat* cformat){
	jobject format = NULL;
	if(Env != NULL && cformat != NULL){
		jclass cls = Env->FindClass("com/mti/primitives/devices/AudioMediaFormat");
		if(cls != NULL){
			jmethodID constructor = Env->GetMethodID(cls, "<init>", "(III)V");
			if(constructor != NULL){
                                format = Env->NewObject(cls, constructor, cformat->BitsPerSample, cformat->Channels, cformat->SampleRate);
			}
		}
	}

	return format;
}

static void Add_jAudioMediaFormat_To_jAudioInputDevice(JNIEnv* Env, jobject jinputDevice, AudioMediaFormat* cformat){
	if(Env != NULL && jinputDevice != NULL && cformat != NULL){
		jclass cls = Env->GetObjectClass(jinputDevice);
		if(cls != NULL){
			jfieldID formatsID = Env->GetFieldID(cls, "Formats", "Ljava/util/List;");
			if(formatsID != NULL){
				jobject formats = Env->GetObjectField(jinputDevice, formatsID);
				if(formats != NULL){
					jclass formatscls = Env->GetObjectClass(formats);
					if(formatscls != NULL){
						jmethodID addmethod = Env->GetMethodID(formatscls, "add", "(Ljava/lang/Object;)Z");
						if(addmethod != NULL){
							jobject jformat = New_jAudioMediaFormat(Env, cformat);
							if(jformat != NULL){
								Env->CallBooleanMethod(formats, addmethod, jformat);
							}
						}
					}	
				}
			}
		}
		
	}
}

static void Add_jAudioMediaFormat_To_jAudioOutputDevice(JNIEnv* Env, jobject joutputDevice, AudioMediaFormat* cformat){
	if(Env != NULL && joutputDevice != NULL && cformat != NULL){
		jclass cls = Env->GetObjectClass(joutputDevice);
		if(cls != NULL){
			jfieldID formatsID = Env->GetFieldID(cls, "Formats", "Ljava/util/List;");
			if(formatsID != NULL){
				jobject formats = Env->GetObjectField(joutputDevice, formatsID);
				if(formats != NULL){
					jclass formatscls = Env->GetObjectClass(formats);
					if(formatscls != NULL){
						jmethodID addmethod = Env->GetMethodID(formatscls, "add", "(Ljava/lang/Object;)Z");
						if(addmethod != NULL){
							jobject jformat = New_jAudioMediaFormat(Env, cformat);
							if(jformat != NULL){
								Env->CallBooleanMethod(formats, addmethod, jformat);
							}
						}
					}	
				}
			}
		}
		
	}
}

static VideoMediaFormat* New_VideoMediaFormat(JNIEnv* Env, jobject jformat){
	VideoMediaFormat* cformat = NULL;
	if(Env != NULL && jformat != NULL){
		jclass formatcls = Env->GetObjectClass(jformat);
		if(formatcls != NULL){
			jfieldID widthfld = Env->GetFieldID(formatcls, "Width", "I");
			jfieldID heightfld = Env->GetFieldID(formatcls, "Height", "I");
			jfieldID fpsfld = Env->GetFieldID(formatcls, "FPS", "I");
			jfieldID pixelfld = Env->GetFieldID(formatcls, "PixelFormat", "Lcom/mti/primitives/devices/VideoPixelFormat;");
			if(widthfld != NULL && heightfld != NULL && fpsfld != NULL && pixelfld != NULL){
				jint width = Env->GetIntField(jformat, widthfld);
				jint height = Env->GetIntField(jformat, heightfld);
				jint fps = Env->GetIntField(jformat, fpsfld);
				jobject pixobject = Env->GetObjectField(jformat, pixelfld);
				int pixelFormat = 0;
				if(pixobject != NULL)
				{
					jclass pixcls = Env->GetObjectClass(pixobject);
					if(pixcls != NULL){
						jmethodID nativeid = Env->GetMethodID(pixcls, "ToNative", "()I");
						if(nativeid != NULL){
							pixelFormat = Env->CallIntMethod(pixobject, nativeid);
						}
					}
					
				}
				cformat = new VideoMediaFormat();
				cformat->Width = width;
				cformat->Height= height;
				cformat->FPS   = fps;
				cformat->PixelFormat = (VideoPixelFormat)pixelFormat;
			}
		}
	}
	return cformat;
}

static AudioMediaFormat* New_AudioMediaFormat(JNIEnv* Env, jobject jformat){
	AudioMediaFormat* cformat = NULL;
	if(Env != NULL && jformat != NULL){
		jclass formatcls = Env->GetObjectClass(jformat);
		if(formatcls != NULL){
			jfieldID sampleratefld = Env->GetFieldID(formatcls, "SampleRate", "I");
			jfieldID bpsfld = Env->GetFieldID(formatcls, "BitsPerSample", "I");
			jfieldID channelsfld = Env->GetFieldID(formatcls, "Channels", "I");
			if(sampleratefld != NULL && bpsfld != NULL && channelsfld != NULL){
				jint samplerate = Env->GetIntField(jformat, sampleratefld);
				jint bps = Env->GetIntField(jformat, bpsfld);
				jint channels = Env->GetIntField(jformat, channelsfld);
				
				cformat = new AudioMediaFormat();
				cformat->SampleRate = samplerate;
				cformat->BitsPerSample= bps;
				cformat->Channels   = channels;
			}
		}
	}
	return cformat;
}

/**
* Creates a new Java VideoInputDevice
*/
static jobject New_jVideoInputDevice(JNIEnv* Env){
	jobject retobj = NULL;
	jclass cls = Env->FindClass("com/mti/primitives/devices/VideoInputDevice");
	if(cls != NULL){
		jmethodID method = Env->GetMethodID(cls, "<init>", "(ILjava/lang/String;)V");
		if(method != NULL){
			jstring str = Env->NewStringUTF("");
			retobj = Env->NewObject(cls, method, 0, str);
		}
	}

	return retobj;
}

/**
* Creates a new Java VideoInputDevice based on the given C++ VideoInputDevice
* cvideo: an instantiated C++ video input device object from which to obtain the definition for the Java version.
*/
static jobject New_jVideoInputDevice(JNIEnv* Env, VideoInputDevice* cvideo){
	jobject retobj = NULL;
	jclass cls = Env->FindClass("com/mti/primitives/devices/VideoInputDevice");
	if(cls != NULL){
		jmethodID method = Env->GetMethodID(cls, "<init>", "(ILjava/lang/String;)V");
		if(method != NULL){
			jstring str = Env->NewStringUTF(cvideo->DeviceName.c_str());
			retobj = Env->NewObject(cls, method, cvideo->DeviceIndex, str);
			if(retobj != NULL){
				for(int x = 0; x < cvideo->Formats.size(); x++)
				{
					Add_jVideoMediaFormat_To_jVideoInputDevice(Env, retobj, (VideoMediaFormat*)cvideo->Formats[x]);
				}
			}
		}
	}
	return retobj;
}

static jobject New_jAudioInputDevice(JNIEnv* Env, AudioInputDevice* caudio){
	jobject retobj = NULL;
	jclass cls = Env->FindClass("com/mti/primitives/devices/AudioInputDevice");
	if(cls != NULL){
		jmethodID method = Env->GetMethodID(cls, "<init>", "(ILjava/lang/String;)V");
		if(method != NULL){
			jstring str = Env->NewStringUTF(caudio->DeviceName.c_str());
			retobj = Env->NewObject(cls, method, caudio->DeviceIndex, str);
			if(retobj != NULL){
				for(int x = 0; x < caudio->Formats.size(); x++)
				{
					Add_jAudioMediaFormat_To_jAudioInputDevice(Env, retobj, (AudioMediaFormat*)caudio->Formats[x]);
				}
			}
		}
	}
	return retobj;
}

/**
* Converts a Java VideoInputDevice object to a c++ videoinputdevice object. Both must be instantiated.
* jvideo: the Java VideoInputDevice object to use as the template for the C++ object.
* cvideo: The instantiated C++ VideoInputDevice object to fill with the information from the Java object.
*/
static void Java_To_VideoInputDevice(JNIEnv* Env, jobject jvideo, VideoInputDevice* cvideo){
	if(Env != NULL && jvideo != NULL && cvideo != NULL)
	{
		jclass cls = Env->GetObjectClass(jvideo);
		if(cls != NULL){
			jfieldID indexfld = Env->GetFieldID(cls, "DeviceIndex", "I");
			jfieldID namefld = Env->GetFieldID(cls, "DeviceName", "Ljava/lang/String;");
			if(indexfld != NULL && namefld != NULL){
				jstring jname = (jstring)Env->GetObjectField(jvideo, namefld);
				jint jindex = Env->GetIntField(jvideo, indexfld);
				cvideo->DeviceIndex = (int)jindex;
				cvideo->DeviceName = Env->GetStringUTFChars(jname,NULL);
			}
		}
	}
}

static void Java_To_AudioInputDevice(JNIEnv* Env, jobject jaudio, AudioInputDevice* caudio){
	if(Env != NULL && jaudio != NULL && caudio != NULL)
	{
		jclass cls = Env->GetObjectClass(jaudio);
		if(cls != NULL){
			jfieldID indexfld = Env->GetFieldID(cls, "DeviceIndex", "I");
			jfieldID namefld = Env->GetFieldID(cls, "DeviceName", "Ljava/lang/String;");
			if(indexfld != NULL && namefld != NULL){
				jstring jname = (jstring)Env->GetObjectField(jaudio, namefld);
				jint jindex = Env->GetIntField(jaudio, indexfld);
				caudio->DeviceIndex = (int)jindex;
				caudio->DeviceName = Env->GetStringUTFChars(jname,NULL);
			}
		}
	}
}