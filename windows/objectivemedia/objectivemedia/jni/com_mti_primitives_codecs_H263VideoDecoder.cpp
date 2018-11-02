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
#include "com_mti_primitives_codecs.h"
#include "com_mti_primitives_devices.h"

H263VideoDecoder* H263Decoder = NULL;
/*
 * Class:     com_mti_primitives_codecs_H263VideoDecoder
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/VideoMediaFormat;Lcom/mti/primitives/codecs/CodecData;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoDecoder_PlatformOpen
  (JNIEnv * Env, jobject sender, jobject format, jobject codecData){
	  jint retval = 0;
	  if(format != NULL && codecData != NULL){
		  VideoMediaFormat* cformat = New_VideoMediaFormat(Env, format);
		  CodecData* cdata = New_CodecData(Env, codecData);
		  if(cformat != NULL && cdata != NULL){
			  H263Decoder = new H263VideoDecoder();
			  retval = H263Decoder->Open(cformat, cdata);
			  if(retval != 0){
				  delete(cformat);
				  delete(cdata);
			  }
		  }
		  else{
			  retval = Codec_Errors::CODEC_INVALID_INPUT;
			  delete(cformat);
			  delete(cdata);
		  }
		  
	  }
	  else{
		  retval = Codec_Errors::CODEC_INVALID_INPUT;
	  }
	  
	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoDecoder
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoDecoder_PlatformClose
  (JNIEnv * Env, jobject sender){
	  jint retval = 0;
	  if(H263Decoder != NULL){
		  retval = H263Decoder->Close();
		  delete(H263Decoder->CurrentFormat);
		  delete(H263Decoder->CurrentData);
		  delete(H263Decoder);
		  H263Decoder = NULL;
	  }
	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoDecoder
 * Method:    PlatformEncode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoDecoder_PlatformEncode
  (JNIEnv * Env, jobject sender, jbyteArray Sample, jobject encSample, jlong timestamp){
	  return Codec_Errors::CODEC_NOT_SUPPORTED;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoDecoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoDecoder_PlatformDecode
  (JNIEnv * Env, jobject sender, jbyteArray encSample, jobject decSample, jlong timestamp){
	  jint retval = 0;
	  if(encSample == NULL){
		  retval = Codec_Errors::CODEC_INVALID_INPUT;
	  }
	  else if(H263Decoder == NULL){
		  retval = Codec_Errors::CODEC_CODEC_NOT_OPENED;
	  }
	  else{
		  jbyte* inSample;
		  long inlen = Env->GetArrayLength(encSample);
		  jbyte* outSample;
		  inSample = new jbyte[inlen];
		  Env->GetByteArrayRegion(encSample,0,inlen,inSample);
		  long outsize = 0;
		  retval = H263Decoder->Decode((void*)inSample,inlen, (void**)&outSample,&outsize, timestamp);
		  delete(inSample);
		  if(retval == 0){
			  
			  if(decSample == NULL)
			  {
				  retval = Codec_Errors::CODEC_NO_OUTPUT;
			  }
			  else{
				  Sample_To_CodecResult(Env, outSample, outsize, decSample, timestamp);
			
			  }
			  av_free(outSample);
		  }
	  }

	  return retval;
}