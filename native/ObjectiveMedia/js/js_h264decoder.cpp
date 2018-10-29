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
#include "js_h264decoder.h"
H264VideoDecoder* H264Decoder = NULL;

/**
 * Opens an H.264 decoder for use in future decoder.
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
EMSCRIPTEN_KEEPALIVE int js_H264VideoDecoder_PlatformOpen(int videoType, int width, int height, int fps, int pixelFormat, int bitRate, int isVBS, int quality, int crispness, int kfs){
	int retval = 0;
	VideoMediaFormat* cformat = new VideoMediaFormat();

	CodecData* cdata = new CodecData();
	cformat->VideoType = videoType;
	cformat->Width = width;
	cformat->Height = height;
	cformat->FPS = fps;
	cformat->PixelFormat = (VideoPixelFormat)pixelFormat;
	cdata->BitRate = bitRate;
	cdata->IsVariableBitRate = isVBS;
	cdata->Quality = quality;
	cdata->Crispness = crispness;
	cdata->KeyFrameSpace = kfs;
	H264Decoder = new H264VideoDecoder();
	retval = H264Decoder->Open(cformat, cdata);
	if(retval != 0){
		delete(cformat);
		delete(cdata);
	}
	return retval;
}

/**
 * Closes the decoder.
 */
EMSCRIPTEN_KEEPALIVE int js_H264VideoDecoder_PlatformClose(){
	  int retval = 0;
	  if(H264Decoder != NULL){
		  retval = H264Decoder->Close();
		  delete(H264Decoder->CurrentFormat);
		  delete(H264Decoder->CurrentData);
		  delete(H264Decoder);
		  H264Decoder = NULL;
	  }
	  return retval;
}

/**
 * Not implemented, returns null.
 */
EMSCRIPTEN_KEEPALIVE unsigned char* js_H264VideoDecoder_PlatformEncode(char* sample, int size, long timestamp){
	return NULL;
}

/**
 * Decodes an H.263+ frame. This function returns a byte array, with the first four bytes of the array representing an integer value
 * of the size of the array, and the rest of the array containing the decoded frame.
 * sample: The encoded data to be decoded.
 * size: the size of the encoded data.
 * timestamp: the time stamp of the encoded data.
 */
EMSCRIPTEN_KEEPALIVE unsigned char* js_H264VideoDecoder_PlatformDecode(char* sample, int size, long timestamp){
	  unsigned char* retval;
	  if(sample == NULL){
		  retval = NULL;
	  }	  
	  else if(H264Decoder == NULL){
		  retval = NULL;
	  }
	  else{
		  long outsize = 0;
		  unsigned char* result;
		  int r = H264Decoder->Decode((void*)sample,size, (void**)&result,&outsize, timestamp);

		  if(r != 0){
			  retval = NULL;
		  }
		  else{
			  retval = (unsigned char*)malloc(outsize + 4);
			  unsigned char* sizebytes = (unsigned char*) &outsize;
			  memcpy((void*) retval, (void*) sizebytes, 4);
			  unsigned char* next = retval+4;
			  memcpy((void*) next, (void*) result, outsize);
		  }
	  }

	  return retval;
}