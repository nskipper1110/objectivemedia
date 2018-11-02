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

G7231AudioEncoder* G7231Encoder = NULL;
/*
 * Class:     com_mti_primitives_codecs_G7231AudioEncoder
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/AudioMediaFormat;Lcom/mti/primitives/codecs/CodecData;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioEncoder_PlatformOpen
  (JNIEnv * Env, jobject sender, jobject format, jobject codecData){
	  jint retval = 0;
	  if(format != NULL && codecData != NULL){
		  AudioMediaFormat* cformat = New_AudioMediaFormat(Env, format);
		  CodecData* cdata = New_CodecData(Env, codecData);
		  if(cformat != NULL && cdata != NULL){
			  G7231Encoder = new G7231AudioEncoder();
			  retval = G7231Encoder->Open(cformat, cdata);
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
 * Class:     com_mti_primitives_codecs_G7231AudioEncoder
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioEncoder_PlatformClose
  (JNIEnv * Env, jobject sender){
	  jint retval = 0;
	  if(G7231Encoder != NULL){
		  retval = G7231Encoder->Close();
		  delete(G7231Encoder->CurrentFormat);
		  delete(G7231Encoder->CurrentData);
		  delete(G7231Encoder);
		  G7231Encoder = NULL;
	  }
	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_G7231AudioEncoder
 * Method:    PlatformEncode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioEncoder_PlatformEncode
  (JNIEnv * Env, jobject sender, jbyteArray Sample, jobject encSample, jlong timestamp){
	  jint retval = 0;
	  if(Sample == NULL){
		  retval = Codec_Errors::CODEC_INVALID_INPUT;
	  }
	  else if(G7231Encoder == NULL){
		  retval = Codec_Errors::CODEC_CODEC_NOT_OPENED;
	  }
	  else{
		  jbyte* inSample;
		  long inlen = Env->GetArrayLength(Sample);
		  jbyte* outSample;
		  inSample = new jbyte[inlen];
		  Env->GetByteArrayRegion(Sample,0,inlen,inSample);
		  long outsize = 0;
		  retval = G7231Encoder->Encode((void*)inSample,inlen, (void**)&outSample,&outsize, timestamp);
		  delete(inSample);
		  if(retval == 0){
			  
			  if(encSample == NULL)
			  {
				  retval = Codec_Errors::CODEC_NO_OUTPUT;
			  }
			  else{
				  Sample_To_CodecResult(Env, outSample, outsize, encSample, timestamp);
			
			  }
			  av_free(outSample);
		  }
	  }

	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_G7231AudioEncoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioEncoder_PlatformDecode
  (JNIEnv * Env, jobject sender, jbyteArray encSample, jobject decSample, jlong timestamp){
	  return Codec_Errors::CODEC_NOT_SUPPORTED;
}
