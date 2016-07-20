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
#pragma once

#include "com_mti_primitives_codecs_H263VideoEncoder.h"
#include "com_mti_primitives_codecs_H263VideoDecoder.h"
#include "com_mti_primitives_codecs_VC1VideoDecoder.h"
#include "com_mti_primitives_codecs_G7231AudioDecoder.h"
#include "com_mti_primitives_codecs_G7231AudioEncoder.h"

#include "../platform/platform_codecs.h"

static CodecData* New_CodecData(JNIEnv* Env, jobject jdata){
	CodecData* cdata = NULL;
	if(Env != NULL && jdata != NULL){
		jclass datacls = Env->GetObjectClass(jdata);
		if(datacls != NULL){
			jfieldID bitrateid = Env->GetFieldID(datacls, "BitRate", "I");
			jfieldID qualityid = Env->GetFieldID(datacls, "Quality", "I");
			jfieldID vbrid = Env->GetFieldID(datacls, "IsVariableBitRate", "Z");
			jfieldID crispid = Env->GetFieldID(datacls, "Crispness", "I");
			jfieldID kpsid = Env->GetFieldID(datacls, "KeyFrameSpace", "I");
			if(bitrateid != NULL && qualityid != NULL && vbrid != NULL && crispid != NULL && kpsid != NULL){
				cdata = new CodecData();
				cdata->BitRate = Env->GetIntField(jdata, bitrateid);
				cdata->Quality = Env->GetIntField(jdata, qualityid);
				cdata->IsVariableBitRate = Env->GetBooleanField(jdata, vbrid);
				cdata->Crispness = Env->GetIntField(jdata, crispid);
				cdata->KeyFrameSpace = Env->GetIntField(jdata, kpsid);
			}
		}
	}
	return cdata;
}

static bool Sample_To_CodecResult(JNIEnv* Env, jbyte* sample, int size, jobject codecResult, jlong timestamp){
	bool retval = true;
	if(sample == NULL || size <= 0 || codecResult == NULL){
		retval = false;
	}
	else{
		jclass cls = Env->GetObjectClass(codecResult);
		jmethodID method = Env->GetMethodID(cls, "SetResult", "([BJ)V");
		if(cls == NULL || method == NULL){
			retval = false;
		}
		else{
			jbyteArray output = Env->NewByteArray(size);
			Env->SetByteArrayRegion(output, 0, size, sample);
			Env->CallVoidMethod(codecResult, method, output, timestamp);
		}
	}
	return retval;
}