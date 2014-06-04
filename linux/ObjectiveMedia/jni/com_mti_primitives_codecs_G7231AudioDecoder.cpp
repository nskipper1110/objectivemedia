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
                      jclass ccls = Env->GetObjectClass(sender);
                      ccls = Env->GetSuperclass(ccls);
                      jfieldID fld = Env->GetFieldID(ccls, "Primitive", "J");
                      G7231AudioDecoder* pG7231Decoder = new G7231AudioDecoder();
                      //H263Decoder = new H263VideoDecoder();
                      jlong pint = (jlong)pG7231Decoder;
                      Env->SetLongField(sender, fld, pint);
                      retval = pG7231Decoder->Open(cformat, cdata);
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
 * Class:     com_mti_primitives_codecs_G7231AudioDecoder
 * Method:    PlatformClose
 * Signature: ()I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioDecoder_PlatformClose
  (JNIEnv * Env, jobject sender){
	  jint retval = 0;
          jclass ccls = Env->GetObjectClass(sender);
          ccls = Env->GetSuperclass(ccls);
          jfieldID fld = Env->GetFieldID(ccls, "Primitive", "J");
          G7231AudioDecoder* pG7231Decoder = (G7231AudioDecoder*)Env->GetLongField(sender, fld);
	  if(pG7231Decoder != NULL){
		  retval = pG7231Decoder->Close();
		  delete(pG7231Decoder->CurrentFormat);
		  delete(pG7231Decoder->CurrentData);
		  delete(pG7231Decoder);
		  pG7231Decoder = NULL;
                  Env->SetLongField(sender, fld, 0);
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
	  return CODEC_NOT_SUPPORTED;
}

/*
 * Class:     com_mti_primitives_codecs_G7231AudioDecoder
 * Method:    PlatformDecode
 * Signature: ([B[BJ)I
 */
JNIEXPORT jint JNICALL Java_com_mti_primitives_codecs_G7231AudioDecoder_PlatformDecode
  (JNIEnv * Env, jobject sender, jbyteArray encSample, jobject decSample, jlong timestamp){
	  jint retval = 0;
          jclass ccls = Env->GetObjectClass(sender);
          ccls = Env->GetSuperclass(ccls);
          jfieldID fld = Env->GetFieldID(ccls, "Primitive", "J");
          G7231AudioDecoder* pG7231Decoder = (G7231AudioDecoder*)Env->GetLongField(sender, fld);
	  
	  if(encSample == NULL){
		  retval = CODEC_INVALID_INPUT;
	  }
	  else if(pG7231Decoder == NULL){
		  retval = CODEC_CODEC_NOT_OPENED;
	  }
	  else{
                  
		  jbyte* inSample = Env->GetByteArrayElements(encSample, NULL);
		  long inlen = Env->GetArrayLength(encSample);
		  jbyte* outSample;
		  //inSample = new jbyte[inlen];
		  //Env->GetByteArrayRegion(encSample,0,inlen,inSample);
		  long outsize = 0;
		  retval = pG7231Decoder->Decode((void*)inSample,inlen, (void**)&outSample,&outsize, timestamp);
                  
                  Env->ReleaseByteArrayElements(encSample, inSample, JNI_ABORT);//delete(inSample);
		  if(retval == 0){
			  
			  if(decSample == NULL)
			  {
				  retval = CODEC_NO_OUTPUT;
			  }
			  else{
				  Sample_To_CodecResult(Env, outSample, 480, decSample, timestamp);
			
			  }
			  //free(outSample);
		  }
	  }

	  return retval;
}
