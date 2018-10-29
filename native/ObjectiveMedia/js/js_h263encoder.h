/*
 * copyright (c) 2018 Nathan Skipper, Montgomery Technology, Inc.
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

#ifndef _Included_js_H263VideoEncoder
#define _Included_js_H263VideoEncoder
#include "js_includes.h"
#ifdef __cplusplus
extern "C" {
#endif
/**
 * Opens an H.263p encoder for use in future encoding.
 * Parameters:
 * videoType: A platform specific reference to the type of video being encoded. Currently not used.
 * width: The width, in pixels, of the video frame.
 * height: the height, in pixels, of the video frame.
 * pixelFormat: the pixel format of the frame. This is an enumerated value defined by the VideoPxelFormat enumerator (see platform_includes.h)
 * bitRate: the bit rate, in bits per second, at which the video should be encoded.
 * isVBS: a binary value (0 or 1) designating whether variable bit rate encoding should be used. Not used for this encoder.
 * quality: the quality (percentage) of encoding. 0 to 100.
 * Crispness: The quality of crispness between frames. Not used in this encoder.
 * kfs: The space, in number of frames, between key frames.
 */
EMSCRIPTEN_KEEPALIVE int js_H263VideoEncoder_PlatformOpen(int videoType, int width, int height, int fps, int pixelFormat, int bitRate, int isVBS, int quality, int crispness, int kfs);

/**
 * Closes the encoder.
 */
EMSCRIPTEN_KEEPALIVE int js_H263VideoEncoder_PlatformClose();

/**
 * Encodes a video frame and returns the resulting encoded bytes, with the first four bytes of the encoded frame byte array
 * representing the size of the array.
 * Parameters:
 * Sample: the video frame to encode.
 * size: the size of the video frame, in bytes.
 * timestamp: the time stamp, in milliseconds, at which the sample was acquired.
 */
EMSCRIPTEN_KEEPALIVE unsigned char* js_H263VideoEncoder_PlatformEncode(char* sample, int size, long timestamp);

/**
 * The decode is not implemented for the encoder.
 * Returns null.
 */
EMSCRIPTEN_KEEPALIVE unsigned char* js_H263VideoEncoder_PlatformDecode(char* sample, int size, long timestamp);



#ifdef __cplusplus
}
#endif
#endif
