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
#include <libavcodec/avcodec.h>
#include <libavutil/mathematics.h>
#include <libavutil/samplefmt.h>
#include <libavformat/avformat.h>
#include <libswscale/swscale.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
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
};

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

	static AVFrame *alloc_picture(enum PixelFormat pix_fmt, int width, int height)
	{
		AVFrame *picture;
		unsigned char*picture_buf;
		int size;

		picture = avcodec_alloc_frame();
		if (!picture)
			return NULL;
		size        = avpicture_get_size(pix_fmt, width, height);
		picture_buf = (unsigned char*)av_malloc(size);
		if (!picture_buf) {
			av_free(picture);
			return NULL;
		}
		avpicture_fill((AVPicture *)picture, picture_buf,
					   pix_fmt, width, height);
		return picture;
	}

	static AVFrame *alloc_and_fill_picture(enum PixelFormat pix_fmt, int width, int height, void* buf)
	{
		AVFrame *picture;
		picture = avcodec_alloc_frame();
		if (!picture)
			return NULL;
		
		avpicture_fill((AVPicture *)picture, (unsigned char*)buf,
					   pix_fmt, width, height);
		return picture;
	}

	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	Codec_Errors Close();
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
};

#endif