#include "com_mti_primitives_devices.h"

AudioInputDevice* AudioInput = NULL;
static JavaVM* CallbackJVM = NULL;
static jobject MyListener = NULL;
static jobject jaudioInputDevice = NULL;

class AudioInputDeviceListener : public DeviceListener
{
	void SampleCaptured(void* sender, void* sample, long size, long long timestamp)
	{
		//DebugOut("VideoInputDeviceListener.SampleCaptured++\n");
		if(MyListener != NULL && CallbackJVM != NULL)
		{
			//DebugOut("Listener and JVM are instantiated.\n");
			JNIEnv* CallbackEnv = NULL;
			//DebugOut("Attaching to current thread.\n");
			if(CallbackJVM->AttachCurrentThread((void**)&CallbackEnv, NULL) == 0)
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
							CallbackEnv->CallVoidMethod(MyListener, id, jaudioInputDevice, frame, tstamp);
						}
					}
				}
				//DebugOut("Detaching thread\n");
				CallbackJVM->DetachCurrentThread();
			}
		
		}
		//DebugOut("VideoInputDeviceListener.SampleCaptured--");
	}
};
/*
 * Class:     com_mti_primitives_devices_AudioInputDevice
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/AudioMediaFormat;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_AudioInputDevice_PlatformOpen
  (JNIEnv * Env, jobject sender, jobject format){
    jint retval = 0;
    try{
        if(Env == NULL || sender == NULL || format == NULL){
            retval = INVALID_DATA;
        }
        else if(Env->GetJavaVM(&CallbackJVM) != 0)
        {
            retval = NOT_SUPPORTED;
        }
        else{
            jclass sendercls = Env->GetObjectClass(sender);
            if(sendercls == NULL){
                retval = INVALID_DATA;
            }
            else{
                jfieldID listenerID = Env->GetFieldID(sendercls, "Listener", "Lcom/mti/primitives/devices/DeviceListener;");
                
                if(listenerID == NULL)
                {
                    retval = INVALID_DATA;
                    
                }
                else{
                    jobject jlistener = Env->GetObjectField(sender, listenerID);
                   if(jlistener != NULL)
                    {
                        AudioInputDevice* tempDevice = new AudioInputDevice();
                        Java_To_AudioInputDevice(Env, sender, tempDevice);
                        std::vector<Device*> deviceList;
                        MyListener = Env->NewGlobalRef(jlistener);
                        jaudioInputDevice = Env->NewGlobalRef(sender);
			  if(tempDevice->GetDevices(deviceList) == SUCCEEDED){
				  AudioInput = (AudioInputDevice*)deviceList[tempDevice->DeviceIndex];
				  for(int x = 0; x < deviceList.size(); x++)
				  {
					  if(x != AudioInput->DeviceIndex)
						  delete deviceList[x];
				  }
				  deviceList.clear();
				  AudioInputDeviceListener* clistener = new AudioInputDeviceListener();
				  AudioInput->Listener = clistener;
				  AudioMediaFormat* cformat = New_AudioMediaFormat(Env, format);
				  retval = (jint)AudioInput->Open(cformat);
			  }
			  else{
				  retval = (jint)NO_DEVICES;
			  }
                        
                    }
                   else{
                       retval = INVALID_DATA;
                   }
                    
                }
                
            }
        }
    }
    catch(...){
        retval = UNEXPECTED;
    }
    return retval;
}

/*
 * Class:     com_mti_primitives_devices_AudioInputDevice
 * Method:    PlatformGetDevices
 * Signature: (Ljava/util/List;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_AudioInputDevice_PlatformGetDevices
  (JNIEnv * Env, jobject sender, jobject deviceList){
    jint retval = 0;
    try{
        jclass listcls = Env->GetObjectClass(deviceList);
        if(listcls == NULL){
            retval = INVALID_DATA;
        }
        else{
            jmethodID addid = Env->GetMethodID(listcls, "add", "(Ljava/lang/Object;)Z");
            if(addid == NULL){
                retval = INVALID_DATA;
            }
            else{
                  AudioInputDevice* vd = new AudioInputDevice();
                  std::vector<Device*> devList;
                  retval = vd->GetDevices(devList);
                  if(retval == SUCCEEDED)
                  {
                          int size = devList.size();
                          for(int x = 0; x < size; x++)
                          {
                              jobject dev = New_jAudioInputDevice(Env, (AudioInputDevice*) devList[x]);
                              delete(devList[x]);
                              Env->CallBooleanMethod(deviceList, addid, dev);
                                  
                          }
                          devList.clear();
                  }
                  delete(vd);
            }
        }
        

    }
    catch(...){
        retval = UNEXPECTED;
    }
    return retval;
}

/*
 * Class:     com_mti_primitives_devices_AudioInputDevice
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_AudioInputDevice_PlatformClose
  (JNIEnv * Env, jobject sender){
    jint retval = 0;
    try{
        if(AudioInput != NULL){
            retval = AudioInput->Close();
            delete(AudioInput);
            AudioInput = NULL;
        }
    }
    catch(...){
        retval = UNEXPECTED;
    }
    return retval;
}
