#include "com_mti_primitives_devices.h"
/*
 * Class:     com_mti_primitives_devices_VideoOutputDevice
 * Method:    PlatformPresent
 * Signature: ([BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoOutputDevice_PlatformPresent
  (JNIEnv * Env, jobject sender, jbyteArray sample, jlong timestamp){
	  return 0;
}

/*
 * Class:     com_mti_primitives_devices_VideoOutputDevice
 * Method:    PlatformGetDevices
 * Signature: ([Lcom/mti/primitives/devices/VideoOutputDevice;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoOutputDevice_PlatformGetDevices
  (JNIEnv * Env, jobject sender, jobjectArray deviceList)
{
	return 0;
}

/*
 * Class:     com_mti_primitives_devices_VideoOutputDevice
 * Method:    PlatformOpen
 * Signature: (IIIIIJIIZ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoOutputDevice_PlatformOpen
  (JNIEnv * Env, jobject sender, jint, jint, jint, jint, jint, jlong, jint, jint, jboolean){
	  return 0;
}

/*
 * Class:     com_mti_primitives_devices_VideoOutputDevice
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoOutputDevice_PlatformClose
  (JNIEnv * Env, jobject sender){
	  return 0;
}