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
#include <emscripten.h>
#include "../platform/platform_codecs.h"
#include "../platform/platform_devices.h"
#ifndef _Included_js_H263VideoEncoder
#define _Included_js_H263VideoEncoder
#ifdef __cplusplus
extern "C" {
#endif

EMSCRIPTEN_KEEPALIVE int js_H263VideoEncoder_PlatformOpen
  (int videoType, int width, int height, int fps, int pixelFormat, int bitRate, int isVBS, int quality, int crispness, int kfs);


EMSCRIPTEN_KEEPALIVE int js_H263VideoEncoder_PlatformClose
  ();


EMSCRIPTEN_KEEPALIVE char* js_H263VideoEncoder_PlatformEncode
  (char* sample, int size, long timestamp);

/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
EMSCRIPTEN_KEEPALIVE char* js_H263VideoEncoder_PlatformDecode
  (char* sample, int size, long timestamp);

#ifdef __cplusplus
}
#endif
#endif
