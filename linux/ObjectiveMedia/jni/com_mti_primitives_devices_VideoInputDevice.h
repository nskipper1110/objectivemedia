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
#include <jni.h>
/* Header for class com_mti_primitives_devices_VideoInputDevice */

#ifndef _Included_com_mti_primitives_devices_VideoInputDevice
#define _Included_com_mti_primitives_devices_VideoInputDevice
#ifdef __cplusplus
extern "C" {
#endif
/*
 * Class:     com_mti_primitives_devices_VideoInputDevice
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/DeviceListener;IIII)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoInputDevice_PlatformOpen
  (JNIEnv *, jobject, jobject, jint, jint, jint, jint);

/*
 * Class:     com_mti_primitives_devices_VideoInputDevice
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoInputDevice_PlatformClose
  (JNIEnv *, jobject);

/*
 * Class:     com_mti_primitives_devices_VideoInputDevice
 * Method:    PlatformGetDevices
 * Signature: ([Lcom/mti/primitives/devices/VideoInputDevice;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_devices_VideoInputDevice_PlatformGetDevices
  (JNIEnv *, jobject, jobjectArray);

#ifdef __cplusplus
}
#endif
#endif
