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

/*
 * Class:     com_mti_primitives_devices_FileOutputDevice
 * Method:    PlatformOpen
 * Signature: (Ljava/lang/String;IIIII)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_FileOutputDevice_PlatformOpen
  (JNIEnv *Env, jobject sender, jstring fileName, jint frameWidth, jint frameHeight, jint sampleRate, jint bitsPerSample, jint channels){
    return NOT_SUPPORTED;
}

/*
 * Class:     com_mti_primitives_devices_FileOutputDevice
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_FileOutputDevice_PlatformClose
  (JNIEnv * Env, jobject sender){
    return NOT_SUPPORTED;
}

/*
 * Class:     com_mti_primitives_devices_FileOutputDevice
 * Method:    PlatformPresentAudio
 * Signature: ([BJJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_FileOutputDevice_PlatformPresentAudio
  (JNIEnv * Env, jobject sender, jbyteArray sample, jlong size, jlong timestamp){
    return NOT_SUPPORTED;
}

/*
 * Class:     com_mti_primitives_devices_FileOutputDevice
 * Method:    PlatformPresentVideo
 * Signature: ([BJJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_FileOutputDevice_PlatformPresentVideo
  (JNIEnv * Env, jobject sender, jbyteArray sample, jlong size, jlong timestamp){
    return NOT_SUPPORTED;
}