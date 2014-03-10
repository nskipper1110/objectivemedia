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

H263VideoEncoder* H263Encoder = NULL;
/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformOpen
 * Signature: (Lcom/mti/primitives/devices/VideoMediaFormat;Lcom/mti/primitives/codecs/CodecData;)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoEncoder_PlatformOpen
  (JNIEnv * Env, jobject sender, jobject format, jobject codecData){
	  jint retval = 0;
	  if(format != NULL && codecData != NULL){
		  VideoMediaFormat* cformat = New_VideoMediaFormat(Env, format);
		  CodecData* cdata = New_CodecData(Env, codecData);
		  if(cformat != NULL && cdata != NULL){
			  H263Encoder = new H263VideoEncoder();
			  retval = H263Encoder->Open(cformat, cdata);
			  if(retval != 0){
				  delete(cformat);
				  delete(cdata);
			  }
		  }
		  else{
			  retval = CODEC_INVALID_INPUT;
			  delete(cformat);
			  delete(cdata);
		  }
		  
	  }
	  else{
		  retval = CODEC_INVALID_INPUT;
	  }
	  
	  return retval;
}

/*
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoEncoder_PlatformClose
  (JNIEnv * Env, jobject sender){
	  jint retval = 0;
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
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoEncoder_PlatformEncode
  (JNIEnv * Env, jobject sender, jbyteArray Sample, jobject encSample, jlong timestamp){
	  jint retval = 0;
	  if(Sample == NULL){
		  retval = CODEC_INVALID_INPUT;
	  }
	  else if(H263Encoder == NULL){
		  retval = CODEC_CODEC_NOT_OPENED;
	  }
	  else{
		  jbyte* inSample = Env->GetByteArrayElements(Sample, NULL);
		  long inlen = Env->GetArrayLength(Sample);

		  jbyte* outSample;
		  //inSample = new jbyte[inlen];
		  //Env->GetByteArrayRegion(Sample,0,inlen,inSample);

		  long outsize = 0;
		  retval = H263Encoder->Encode((void*)inSample,inlen, (void**)&outSample,&outsize, timestamp);

		  Env->ReleaseByteArrayElements(Sample, inSample, JNI_ABORT);//delete(inSample);
		  if(retval == 0){
			  
			  if(encSample == NULL)
			  {
				  retval = CODEC_NO_OUTPUT;
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
 * Class:     com_mti_primitives_codecs_H263VideoEncoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_H263VideoEncoder_PlatformDecode
  (JNIEnv * Env, jobject sender, jbyteArray encSample, jobject decSample, jlong timestamp){
	  return CODEC_NOT_SUPPORTED;
}
