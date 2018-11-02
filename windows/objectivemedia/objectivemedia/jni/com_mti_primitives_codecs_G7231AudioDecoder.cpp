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

G7231AudioDecoder* G7231Decoder = NULL;
/*
 * Class:     com_mti_primitives_codecs_G7231AudioDecoder
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/AudioMediaFormat;Lcom/mti/primitives/codecs/CodecData;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioDecoder_PlatformOpen
  (JNIEnv * Env, jobject sender, jobject format, jobject codecData){
	  jint retval = 0;
	  if(format != NULL && codecData != NULL){
		  AudioMediaFormat* cformat = New_AudioMediaFormat(Env, format);
		  CodecData* cdata = New_CodecData(Env, codecData);
		  if(cformat != NULL && cdata != NULL){
			  G7231Decoder = new G7231AudioDecoder();
			  retval = G7231Decoder->Open(cformat, cdata);
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
 * Class:     com_mti_primitives_codecs_G7231AudioDecoder
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioDecoder_PlatformClose
  (JNIEnv * Env, jobject sender){
	  jint retval = 0;
	  if(G7231Decoder != NULL){
		  retval = G7231Decoder->Close();
		  delete(G7231Decoder->CurrentFormat);
		  delete(G7231Decoder->CurrentData);
		  delete(G7231Decoder);
		  G7231Decoder = NULL;
	  }
	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_G7231AudioDecoder
 * Method:    PlatformEncode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioDecoder_PlatformEncode
  (JNIEnv * Env, jobject sender, jbyteArray Sample, jobject encSample, jlong timestamp){
	  return Codec_Errors::CODEC_NOT_SUPPORTED;
}

/*
 * Class:     com_mti_primitives_codecs_G7231AudioDecoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioDecoder_PlatformDecode
  (JNIEnv * Env, jobject sender, jbyteArray encSample, jobject decSample, jlong timestamp){
	  jint retval = 0;
	  if(encSample == NULL){
		  retval = Codec_Errors::CODEC_INVALID_INPUT;
	  }
	  else if(G7231Decoder == NULL){
		  retval = Codec_Errors::CODEC_CODEC_NOT_OPENED;
	  }
	  else{
		  jbyte* inSample;
		  long inlen = Env->GetArrayLength(encSample);
		  jbyte* outSample;
		  inSample = new jbyte[inlen];
		  Env->GetByteArrayRegion(encSample,0,inlen,inSample);
		  long outsize = 0;
		  retval = G7231Decoder->Decode((void*)inSample,inlen, (void**)&outSample,&outsize, timestamp);
		  delete(inSample);
		  if(retval == 0){
			  
			  if(decSample == NULL)
			  {
				  retval = Codec_Errors::CODEC_NO_OUTPUT;
			  }
			  else{
				  Sample_To_CodecResult(Env, outSample, 480, decSample, timestamp);
			
			  }
			  //av_free(outSample);
		  }
	  }

	  return retval;
}
