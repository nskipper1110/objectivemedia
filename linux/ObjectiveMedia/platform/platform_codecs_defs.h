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

#ifndef CODEC_DEFS
#define CODEC_DEFS

extern "C"{
	#include <libavutil/imgutils.h>
	#include <libavutil/opt.h>
	#include <libavcodec/avcodec.h>
	#include <libavutil/mathematics.h>
	#include <libavutil/samplefmt.h>
        #include <libswscale/swscale.h>
}



#include "platform_includes.h"

typedef enum Codec_Errors{
	CODEC_SUCCEEDED = 0,
	CODEC_NOT_SUPPORTED = 1,
	CODEC_CODEC_NOT_OPENED = 2,
	CODEC_FAILED_TO_OPEN = 3,
	CODEC_UNAVAILABLE = 4,
	CODEC_INVALID_INPUT = 5,
	CODEC_NO_OUTPUT = 6,
	CODEC_UNEXPECTED = 7
}Codec_Errors;

class CodecData{
public:
	int BitRate;
	bool IsVariableBitRate;
	int Quality;
	int Crispness;
	int KeyFrameSpace;
};

class Codec{
public:
	bool Opened;
	MediaFormat* CurrentFormat;
	CodecData* CurrentData;

	AVCodec* FFEncoder;
	AVCodecContext* FFEncoderContext;

	AVCodec* FFDecoder;
	AVCodecContext* FFDecoderContext;
	AVFrame* TempFrame;
	SwsContext* ScaleContext;

	

	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	Codec_Errors Close();
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
};

#endif