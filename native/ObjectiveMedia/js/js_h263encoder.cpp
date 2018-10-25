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
//#include "com_mti_primitives_codecs.h"
//#include "com_mti_primitives_devices.h"
#include "js_h263encoder.h"
H263VideoEncoder* H263Encoder = NULL;
/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/VideoMediaFormat;Lcom/mti/primitives/codecs/CodecData;)I
 */
EMSCRIPTEN_KEEPALIVE int js_H263VideoEncoder_PlatformOpen
  (int videoType, int width, int height, int fps, int pixelFormat, int bitRate, int isVBS, int quality, int crispness, int kfs)
  {
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
	H263Encoder = new H263VideoEncoder();
	retval = H263Encoder->Open(cformat, cdata);
	if(retval != 0){
		delete(cformat);
		delete(cdata);
	}
	return retval;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformClose
 * Signature: ()I
 */
EMSCRIPTEN_KEEPALIVE int js_H263VideoEncoder_PlatformClose
  (){
	  int retval = 0;
	  if(H263Encoder != NULL){
		  retval = H263Encoder->Close();
		  delete(H263Encoder->CurrentFormat);
		  delete(H263Encoder->CurrentData);
		  delete(H263Encoder);
		  H263Encoder = NULL;
	  }
	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformEncode
 * Signature: ([B[BJ)I
 */
EMSCRIPTEN_KEEPALIVE char* js_H263VideoEncoder_PlatformEncode
  (char* Sample, int size, long timestamp){
	  char* retval = NULL;
	  if(Sample == NULL){
		  retval = NULL;
	  }
	  else if(H263Encoder == NULL){
		  retval = NULL;
	  }
	  else{
		  long outsize = 0;
		  int r = H263Encoder->Encode((void*)Sample,size, (void**)&retval,&outsize, timestamp);

		  if(r != 0){
			  
			  retval = NULL;
		  }
	  }

	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
EMSCRIPTEN_KEEPALIVE char* js_H263VideoEncoder_PlatformDecode
  (char* sample, int size, long timestamp){
	  return NULL;
}
