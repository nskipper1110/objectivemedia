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

#include "platform_codecs.h"
#include "platform_devices.h"
//#region H263VideoEncoder
/////////////////////////////////////////////////////////////
// H263VideoEncoder implementation
/////////////////////////////////////////////////////////////

H263VideoEncoder::H263VideoEncoder(){
	//Initialize all global variables to null for later validation checks.
	FFEncoder = NULL;
	FFEncoderContext = NULL;

	FFDecoder = NULL;
	FFDecoderContext = NULL;

	CurrentFormat = NULL;
	CurrentData = NULL;
	ScaleContext = NULL;
	TempFrame = NULL;
}

Codec_Errors H263VideoEncoder::Open(MediaFormat* encFormat, CodecData* encData){
	Codec_Errors retval = CODEC_SUCCEEDED;
	av_log_set_callback(&avlog_cb);
	try
	{
		sprintf(dbg_buffer, "Opening H263VideoEncoder\n");
		DbgOut(dbg_buffer);
		avcodec_register_all(); //initialize codecs.

		CurrentFormat = encFormat; //store format settings.
		CurrentData = encData;
		VideoMediaFormat* vf = (VideoMediaFormat*)encFormat;
		//find the H.263 encoder.
		FFEncoder = avcodec_find_encoder(AV_CODEC_ID_H263P);
		if(!FFEncoder) //if I didn't find it, return not supported.
			retval = CODEC_NOT_SUPPORTED;
		else{
			sprintf(dbg_buffer, "\tFound codec\n");
			DbgOut(dbg_buffer);
			//if we found the encoder, then instantiate the context and set config.
			FFEncoderContext = avcodec_alloc_context3(FFEncoder);
			FFEncoderContext->codec_type = AVMEDIA_TYPE_VIDEO;
			FFEncoderContext->bit_rate = ((double)encData->BitRate/8) / (double)vf->FPS;
			sprintf(dbg_buffer, "\tBit Rate = %d\n", FFEncoderContext->bit_rate);
			DbgOut(dbg_buffer);
			FFEncoderContext->width = vf->Width;
			FFEncoderContext->height = vf->Height;
//			FFEncoderContext->rc_max_rate = FFEncoderContext->bit_rate;
//			FFEncoderContext->rc_min_rate = FFEncoderContext->bit_rate;
//			FFEncoderContext->rc_buffer_size = FFEncoderContext->bit_rate * vf->FPS;
			AVRational fps;
			fps.num = vf->FPS;
			fps.den = 1;
			sprintf(dbg_buffer, "\tFrame Rate = %d\n", vf->FPS);
			DbgOut(dbg_buffer);
			FFEncoderContext->time_base = fps;
			FFEncoderContext->bit_rate_tolerance = FFEncoderContext->bit_rate*av_q2d(FFEncoderContext->time_base);
			
			FFEncoderContext->gop_size = encData->KeyFrameSpace;
			sprintf(dbg_buffer, "\tKFS = %d\n", FFEncoderContext->gop_size);
			DbgOut(dbg_buffer);
			FFEncoderContext->max_b_frames = 0;
			FFEncoderContext->pix_fmt = AV_PIX_FMT_YUV420P;
			TempFrame = alloc_picture(AV_PIX_FMT_YUV420P, vf->Width, vf->Height);
			sprintf(dbg_buffer, "\tWidth= %d, Height = %d, Format = %d\n", vf->Width, vf->Height, vf->PixelFormat);
			DbgOut(dbg_buffer);
			//if the input frame's format is going to be different from our format, then we need to scale.
			AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
			if(fmt != AV_PIX_FMT_YUV420P)
			{
				sprintf(dbg_buffer, "\tInitializing Scaler\n");
				DbgOut(dbg_buffer);
				//instantiate a scaler.
				ScaleContext = sws_getContext(vf->Width, vf->Height,
                                                 fmt,
                                                 vf->Width, vf->Height,
                                                 AV_PIX_FMT_YUV420P,
                                                 SWS_BICUBIC, NULL, NULL, NULL);
			}
			//open the codec.
			int err = avcodec_open2(FFEncoderContext, FFEncoder,NULL);
			sprintf(dbg_buffer, "\tCodec Open returned %d\n", err);
				DbgOut(dbg_buffer);
			if(err < 0){ //if we failed to open, return error.
				retval = CODEC_FAILED_TO_OPEN;
			}
		}
	}
	catch(...)
	{
		retval = CODEC_UNEXPECTED;
	}
	sprintf(dbg_buffer, "Finished opening H263VideoEncoder\n");
	DbgOut(dbg_buffer);
	return retval;
}

Codec_Errors H263VideoEncoder::Close(){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		sprintf(dbg_buffer, "Closing H263VideoEncoder\n");
		DbgOut(dbg_buffer);
		if(FFEncoderContext != NULL){ //if we have instantiated the context, then close the codec and free it.
			sprintf(dbg_buffer, "\tClosing codec\n");
			DbgOut(dbg_buffer);
			avcodec_close(FFEncoderContext);
			sprintf(dbg_buffer, "\tFreeing codec\n");
			DbgOut(dbg_buffer);
			av_free(FFEncoderContext);
			FFEncoderContext = NULL;
			FFEncoder = NULL;
		}
		if(ScaleContext != NULL){ //if we have instantiated the scaler, then delete the reference.
			sprintf(dbg_buffer, "\tFreeing scaler\n");
			DbgOut(dbg_buffer);
			av_free(ScaleContext);
			ScaleContext = NULL;
		}

		if(TempFrame != NULL){//free the temp frame used by the scaler.
			if(TempFrame->data[0] != NULL) {
				sprintf(dbg_buffer, "\tFreeing Frame Data\n");
				DbgOut(dbg_buffer);
				av_free(TempFrame->data[0]);
			}
			sprintf(dbg_buffer, "\tFreeing Frame\n");
			DbgOut(dbg_buffer);
			av_free(TempFrame);
			TempFrame = NULL;
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	sprintf(dbg_buffer, "Closed H263VideoEncoder\n");
	DbgOut(dbg_buffer);
	return retval;
}


Codec_Errors H263VideoEncoder::Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_SUCCEEDED;
	#ifdef __JS__
	sprintf(dbg_buffer, "H263VideoEncoder::Encode++\n");
	DbgOut(dbg_buffer);
	#endif
	try{
		VideoMediaFormat* vf = (VideoMediaFormat*) CurrentFormat;
		if(vf == NULL){ //if there is no format information, then we haven't opened yet.
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFEncoderContext == NULL){ //if the context isn't instantiated, then we haven't opened yet.
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFEncoder == NULL) //if the encoder isn't instantiated, then we haven't been opened yet.
		{
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else{
			
			#ifdef __JS__
			sprintf(dbg_buffer, "inSample size = %d\n", insize);
			DbgOut(dbg_buffer);
			
			#endif
			//get the FFMpeg equiv. pixel format for the format provided.
			AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
			//if the format of the incoming frame isn't what the encoder expects, then we need to scale.
			#ifdef __JS__
			sprintf(dbg_buffer, "Format = %d, Width = %d, Height = %d\n", vf->PixelFormat, vf->Width, vf->Height);
			DbgOut(dbg_buffer);
			
			#endif
			TempFrame->format = AV_PIX_FMT_YUV420P;
			TempFrame->width = vf->Width;
			TempFrame->height = vf->Height;
			if(fmt != AV_PIX_FMT_YUV420P){
				#ifdef __JS__
				sprintf(dbg_buffer, "Scaling image to match 420 YUV format\n");
				DbgOut(dbg_buffer);
				
				#endif
				AVFrame* tpic = alloc_and_fill_picture(fmt, vf->Width, vf->Height, inSample);
				
				int r = sws_scale(ScaleContext, tpic->data, tpic->linesize,
                      0, vf->Height, TempFrame->data, TempFrame->linesize);
				#ifdef __JS__
				sprintf(dbg_buffer, "Scaled image returned size of %d\n", r);
				DbgOut(dbg_buffer);
				
				#endif
				av_free(tpic);
				tpic = NULL;
			}
			else{ //if there is no need to scale, then copy the incoming frame direct.
				memcpy(TempFrame->data, inSample, insize);
			}
			//create a buffer to receive the compressed frame, with a little padding for good measure.
			//TO-DO: Is this size necessary or beneficial?
			//int outbuf_size = 0;//100000 + 12*vf->Width*vf->Height;
			//void* outbuf = av_malloc(outbuf_size);
			//encode the video frame.
			int got_packet = 0;
			AVPacket pkt;
			av_init_packet(&pkt);
			#ifdef __JS__
			sprintf(dbg_buffer, "Initialized packet\n");
			DbgOut(dbg_buffer);
			
			#endif
			pkt.data = NULL;
			pkt.size = 0;
			avcodec_encode_video2(FFEncoderContext, &pkt, TempFrame, &got_packet);
			#ifdef __JS__
			sprintf(dbg_buffer, "Encoded video with result %d\n", got_packet);
			DbgOut(dbg_buffer);
			
			#endif
			//if the resulting buffer size is 0, then we didn't get anything back from the function.
			//This isn't bad, just means the encoder needs some data to start encoding.
			if(got_packet == 0){
				//av_free(outbuf); //free the buffer
				#ifdef __JS__
				sprintf(dbg_buffer, "Ah! Didn't get a packet!\n");
				DbgOut(dbg_buffer);
				
				#endif
			}
			else{
				*outSample = pkt.data; //set the reference for the outgoing sample.
				#ifdef __JS__
				sprintf(dbg_buffer, "Result size is %d\n", pkt.size);
				DbgOut(dbg_buffer);
				
				#endif
			}
			*outsize = pkt.size; //set the size of the outgoing sample.
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
		#ifdef __JS__
		sprintf(dbg_buffer, "An exception occurred!!!\n");
		DbgOut(dbg_buffer);
		#endif
	}
	#ifdef __JS__
	sprintf(dbg_buffer, "H263VideoEncoder::Encode--, returning %d\n", retval);
	DbgOut(dbg_buffer);
	#endif
	return retval;
}

Codec_Errors H263VideoEncoder::Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_NOT_SUPPORTED;
	try{

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

H263VideoEncoder::~H263VideoEncoder(){
	//if(FFEncoderContext != NULL) Close(); //free the objects by calling close.
}
//#endregion
/////////////////////////////////////////////////////////////
// H263VideoDecoder implementation
/////////////////////////////////////////////////////////////

H263VideoDecoder::H263VideoDecoder(){
	//intialize all global variables to null for validation checking later.
	FFEncoder = NULL;
	FFEncoderContext = NULL;

	FFDecoder = NULL;
	FFDecoderContext = NULL;

	CurrentFormat = NULL;
	CurrentData = NULL;
	TempFrame = NULL;
	ScaleContext = NULL;
}

Codec_Errors H263VideoDecoder::Open(MediaFormat* encFormat, CodecData* encData){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try
	{
		av_log_set_callback(&avlog_cb);
		avcodec_register_all(); //initialize FFMPEG codecs.
		//set global variables.
		CurrentFormat = encFormat;
		CurrentData = encData;
		VideoMediaFormat* vf = (VideoMediaFormat*)encFormat;
		//find the H.263 decoder.
		FFDecoder = avcodec_find_decoder(AV_CODEC_ID_H263);
		if(!FFDecoder) //if it returned null, we didn't find it, exit function.
			retval = CODEC_NOT_SUPPORTED;
		else{ //found decoder, now open.
			//allocate context.
			FFDecoderContext = avcodec_alloc_context3(FFDecoder);
			//open decoder.
			int err = avcodec_open2(FFDecoderContext, FFDecoder, NULL);
			if(err < 0) //if error in open, fail.
				retval = CODEC_FAILED_TO_OPEN;
			else{
				//get the ffmpeg format from the desired output format.
				AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
				TempFrame = alloc_picture(fmt, vf->Width, vf->Height); //allocate temp based on this format.

				if(fmt != AV_PIX_FMT_YUV420P) //if it isn't the standard format, then instantiate the scaler.
				{
				
					ScaleContext = sws_getContext(vf->Width, vf->Height,
													 AV_PIX_FMT_YUV420P,
													 vf->Width, vf->Height,
													 fmt,
													 SWS_BICUBIC, NULL, NULL, NULL);
				}
			}
			
		}
	}
	catch(...)
	{
		retval = CODEC_UNEXPECTED;
	}

	return retval;
}

Codec_Errors H263VideoDecoder::Close(){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		sprintf(dbg_buffer, "Closing H263VideoDecoder\n");
		DbgOut(dbg_buffer);
		if(FFDecoderContext != NULL){ //if we have instantiated the context, then close the codec and free it.
			sprintf(dbg_buffer, "\tClosing H263VideoDecoder Codec Context\n");
			DbgOut(dbg_buffer);
			avcodec_close(FFDecoderContext);
			av_free(FFDecoderContext);
			FFDecoderContext = NULL;
			FFDecoder = NULL;
		}
		if(ScaleContext != NULL){ //if we have instantiated the scaler, then delete the reference.
			sprintf(dbg_buffer, "\tClosing H263VideoDecoder Scaler\n");
			DbgOut(dbg_buffer);
			av_free(ScaleContext);
			ScaleContext = NULL;
		}

		if(TempFrame != NULL){//free the temp frame used by the scaler.
			//if(TempFrame->data[0] != NULL) av_free(TempFrame->data[0]);
			sprintf(dbg_buffer, "\tClosing H263VideoDecoder Temp Frame\n");
			DbgOut(dbg_buffer);
			av_free(TempFrame);
			TempFrame = NULL;
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	sprintf(dbg_buffer, "Closed H263VideoDecoder\n");
	DbgOut(dbg_buffer);
	return retval;
}


Codec_Errors H263VideoDecoder::Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_NOT_SUPPORTED;
	try{

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

Codec_Errors H263VideoDecoder::Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		VideoMediaFormat* vf = (VideoMediaFormat*)CurrentFormat;
		//validate parameters, if not opened, then fail.
		if(vf == NULL){
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFDecoderContext == NULL){
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else{
			//initialize a packet.
			AVPacket avpkt;
			av_init_packet(&avpkt);
			avpkt.size = insize;
			avpkt.data = (unsigned char*) inSample;
			//allocate a picture to receive the decoded frame.
			AVFrame* picture= av_frame_alloc();
			int got_picture, len;
			//decode the packet.
			len = avcodec_decode_video2(FFDecoderContext, picture, &got_picture, &avpkt);
			//if got_picture returned true, then we have a decoded frame!
			if(got_picture != 0){
				//get the desired output format.
				AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
				//if the desired format isn't the decoder format, then we need to scale.
				if(fmt != AV_PIX_FMT_YUV420P){
					//allocate a frame of the desired format.
					AVFrame* tpic = alloc_picture(fmt, vf->Width, vf->Height);
					//scale the frame.
					sws_scale(ScaleContext, picture->data, picture->linesize,
						  0, vf->Height, tpic->data, tpic->linesize);
					//set the outgoing reference.
					*outSample = tpic->data[0];
					//calculate and set the outgoing frame size, in bytes.
					*outsize = picture->width * picture->height * VideoMediaFormat::GetPixelBits(vf->PixelFormat) / 8;
					//free the temporary picture.
					av_free(tpic);
					tpic = NULL;
				}
				else{//if we desire the standard format, then just set the reference and size.
					*outSample = picture->data[0];
					*outsize = picture->width * picture->height * 12 / 8;
				}
			
			}
			else{
				*outsize = 0;
			}
			av_free(picture);
		}
		

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

H263VideoDecoder::~H263VideoDecoder(){
	
}

/////////////////////////////////////////////////////////////
// VC1VideoDecoder implementation
/////////////////////////////////////////////////////////////

VC1VideoDecoder::VC1VideoDecoder(){
	//set all global variables to null for later validation checks.
	FFEncoder = NULL;
	FFEncoderContext = NULL;

	FFDecoder = NULL;
	FFDecoderContext = NULL;

	CurrentFormat = NULL;
	CurrentData = NULL;
	TempFrame = NULL;
	ScaleContext = NULL;
}

Codec_Errors VC1VideoDecoder::Open(MediaFormat* encFormat, CodecData* encData){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try
	{
		av_log_set_callback(&avlog_cb);
		avcodec_register_all(); //load the FFMPEG codecs.
		//set global variables.
		CurrentFormat = encFormat;
		CurrentData = encData;
		VideoMediaFormat* vf = (VideoMediaFormat*)encFormat;
		//find the decoder.
		FFDecoder = avcodec_find_decoder(AV_CODEC_ID_WMV3);
		if(CurrentFormat == NULL){//if no format, fail.
			retval = CODEC_INVALID_INPUT;
		}
		else if(CurrentData == NULL){ //if no codec data, fail.
			retval = CODEC_INVALID_INPUT;
		}
		else if(!FFDecoder) //if no decoder, fail.
			retval = CODEC_NOT_SUPPORTED;
		else{
			//allocate decoder context.
			FFDecoderContext = avcodec_alloc_context3(FFDecoder);
			if(FFDecoderContext == NULL){
				retval = CODEC_FAILED_TO_OPEN;
			}
			else{
				//we need to set the private/extended data to a sequence header for main profile.
				unsigned char ed[16 + FF_INPUT_BUFFER_PADDING_SIZE];
				unsigned char* eds = &ed[0];
				memset(eds, 0, 16 + FF_INPUT_BUFFER_PADDING_SIZE);
				unsigned long val = 0;
				unsigned char* pval = (unsigned char*) &val;
				pval[0] = 75;
				pval[1] = 249;
				pval[2] = 0;
				pval[3] = 1;
				memcpy(eds, pval, 4);

				
				FFDecoderContext->coded_width = vf->Width;
				FFDecoderContext->coded_height = vf->Height;
				
				FFDecoderContext->extradata = (uint8_t*)eds;
				FFDecoderContext->extradata_size = 16;
				//open the codec.
				int err = avcodec_open2(FFDecoderContext, FFDecoder, NULL);
				if(err < 0) //if there was an error, fail.
					retval = CODEC_FAILED_TO_OPEN;
				//load the desired output format.
				AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
				TempFrame = alloc_picture(fmt, vf->Width, vf->Height);
				//if the desired output format is not standard, then open the scaler.
				if(fmt != AV_PIX_FMT_YUV420P)
				{
				
					ScaleContext = sws_getContext(vf->Width, vf->Height,
													 AV_PIX_FMT_YUV420P,
													 vf->Width, vf->Height,
													 fmt,
													 SWS_BICUBIC, NULL, NULL, NULL);
				}
			}
		}
	}
	catch(...)
	{
		retval = CODEC_UNEXPECTED;
	}

	return retval;
}

Codec_Errors VC1VideoDecoder::Close(){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		if(FFDecoderContext != NULL){
			avcodec_close(FFDecoderContext);
			av_free(FFDecoderContext);
			FFDecoder = NULL;
			FFDecoderContext = NULL;
		}
		
		if(ScaleContext != NULL){
			av_free(ScaleContext);
			ScaleContext = NULL;
		}
		if(TempFrame != NULL){
			av_free(TempFrame->data[0]);
			av_free(TempFrame);
			TempFrame = NULL;
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}


Codec_Errors VC1VideoDecoder::Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_NOT_SUPPORTED;
	try{

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

Codec_Errors VC1VideoDecoder::Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		VideoMediaFormat* vf = (VideoMediaFormat*)CurrentFormat;
		//check for validity.
		if(vf == NULL){
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFDecoderContext == NULL){
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else{
			//Instantiate packet.
			AVPacket avpkt;
			av_init_packet(&avpkt);
			avpkt.size = insize;
			avpkt.data = (unsigned char*) inSample;
			//allocate a frame to receive the decoded frame.
			AVFrame* picture= av_frame_alloc();
			int got_picture, len;
			//decode the frame.
			len = avcodec_decode_video2(FFDecoderContext, picture, &got_picture, &avpkt);
			//if true, then we have a decoded frame!
			if(got_picture != 0){
				//get the desired output format.
				AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
				int linesize = VideoMediaFormat::GetPixelBits(vf->PixelFormat) / 8 * vf->Width;
				//if desired format isn't standard, then we need to scale.
				if(fmt != AV_PIX_FMT_YUV420P){
					//allocate temp picture as desired format.
					AVFrame* tpic = alloc_picture(fmt, vf->Width, vf->Height);
					//scale to desired format.
					sws_scale(ScaleContext, picture->data, picture->linesize,
						  0, vf->Height, tpic->data, tpic->linesize);
					//set output references.
					*outSample = tpic->data[0];
					*outsize = picture->width * picture->height * VideoMediaFormat::GetPixelBits(vf->PixelFormat) / 8;
					av_free(tpic);
					tpic = NULL;
				}
				else{
					*outSample = picture->data[0];
					*outsize = picture->width * picture->height * 12 / 8;
				}
			
			}
			else{
				*outsize = 0;
			}
			av_free(picture);
		}
		

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

VC1VideoDecoder::~VC1VideoDecoder(){
	Close(); //destroy all primitives.
}

/////////////////////////////////////////////////////////////
// G7231AudioEncoder implementation
/////////////////////////////////////////////////////////////

G7231AudioEncoder::G7231AudioEncoder(){
	//Initialize all global variables to null for later validation checks.
	FFEncoder = NULL;
	FFEncoderContext = NULL;

	FFDecoder = NULL;
	FFDecoderContext = NULL;

	CurrentFormat = NULL;
	CurrentData = NULL;
	ScaleContext = NULL;
	TempFrame = NULL;
}

Codec_Errors G7231AudioEncoder::Open(MediaFormat* encFormat, CodecData* encData){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try
	{
		avcodec_register_all(); //initialize codecs.
		av_log_set_callback(&avlog_cb);
		CurrentFormat = encFormat; //store format settings.
		CurrentData = encData;
		AudioMediaFormat* vf = (AudioMediaFormat*)encFormat;
		//find the G.729 encoder.
		FFEncoder = avcodec_find_encoder(AV_CODEC_ID_G723_1);
		if(!FFEncoder) //if I didn't find it, return not supported.
			retval = CODEC_NOT_SUPPORTED;
		else{
			//if we found the encoder, then instantiate the context and set config.
			FFEncoderContext = avcodec_alloc_context3(FFEncoder);
			FFEncoderContext->codec_type = AVMEDIA_TYPE_AUDIO;
			FFEncoderContext->bit_rate = encData->BitRate;
			
			FFEncoderContext->sample_rate = vf->SampleRate;
			FFEncoderContext->channels = vf->Channels;
			switch(vf->BitsPerSample)
			{
			case 8:
				FFEncoderContext->sample_fmt = AV_SAMPLE_FMT_U8;
			case 16:
				FFEncoderContext->sample_fmt = AV_SAMPLE_FMT_S16;
			}
			

			int err = avcodec_open2(FFEncoderContext, FFEncoder, NULL);
			if(err < 0){ //if we failed to open, return error.
				retval = CODEC_FAILED_TO_OPEN;
			}
		}
	}
	catch(...)
	{
		retval = CODEC_UNEXPECTED;
	}

	return retval;
}

Codec_Errors G7231AudioEncoder::Close(){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		if(FFEncoderContext != NULL){ //if we have instantiated the context, then close the codec and free it.
			avcodec_close(FFEncoderContext);
			av_free(FFEncoderContext);
			FFEncoderContext = NULL;
			FFEncoder = NULL;
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}


Codec_Errors G7231AudioEncoder::Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		AudioMediaFormat* vf = (AudioMediaFormat*) CurrentFormat;
		if(vf == NULL){ //if there is no format information, then we haven't opened yet.
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFEncoderContext == NULL){ //if the context isn't instantiated, then we haven't opened yet.
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFEncoder == NULL) //if the encoder isn't instantiated, then we haven't been opened yet.
		{
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else{
			//encode the Audio frame.
			AVPacket pack;
			av_init_packet(&pack);
			pack.data = NULL;
			pack.size = 0;
			AVFrame* frame = av_frame_alloc();
			AVSampleFormat fmt = AV_SAMPLE_FMT_S16;
			if(vf->BitsPerSample == 8){
				fmt = AV_SAMPLE_FMT_U8;
			}
			int ret = 0;
			frame->data[0] = (unsigned char*)inSample;
			frame->linesize[0] = insize;
			frame->nb_samples = insize / (vf->BitsPerSample / 8);
			if(ret < 0){
				retval = CODEC_INVALID_INPUT;
			}
			else{
				int got_it = 0;
				ret = avcodec_encode_audio2(FFEncoderContext, &pack, frame, &got_it);
				*outSample = NULL;
				*outsize = 0;
				if(ret == 0){
					if(got_it > 0){
						*outSample = pack.data;
						*outsize = pack.size;

					}
				}
				//av_free(frame->data[0]);
				av_free(frame);
				//av_free(pack.data);
			}
			
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

Codec_Errors G7231AudioEncoder::Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_NOT_SUPPORTED;
	try{

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

G7231AudioEncoder::~G7231AudioEncoder(){
	//Close(); //free the objects by calling close.
}

/////////////////////////////////////////////////////////////
// G7231AudioDecoder implementation
/////////////////////////////////////////////////////////////

G7231AudioDecoder::G7231AudioDecoder(){
	//Initialize all global variables to null for later validation checks.
	FFDecoder = NULL;
	FFDecoderContext = NULL;

	FFDecoder = NULL;
	FFDecoderContext = NULL;

	CurrentFormat = NULL;
	CurrentData = NULL;
	ScaleContext = NULL;
	TempFrame = NULL;
}

Codec_Errors G7231AudioDecoder::Open(MediaFormat* encFormat, CodecData* encData){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try
	{
		avcodec_register_all(); //initialize codecs.
		av_log_set_callback(&avlog_cb);
		CurrentFormat = encFormat; //store format settings.
		CurrentData = encData;
		AudioMediaFormat* vf = (AudioMediaFormat*)encFormat;
		//find the G.729 Decoder.
		FFDecoder = avcodec_find_decoder(AV_CODEC_ID_G723_1);
		if(!FFDecoder) //if I didn't find it, return not supported.
			retval = CODEC_NOT_SUPPORTED;
		else{
			//if we found the Decoder, then instantiate the context and set config.
			FFDecoderContext = avcodec_alloc_context3(FFDecoder);
			FFDecoderContext->codec_type = AVMEDIA_TYPE_AUDIO;
			FFDecoderContext->bit_rate = encData->BitRate;
			
			FFDecoderContext->sample_rate = vf->SampleRate;
			FFDecoderContext->channels = vf->Channels;
			switch(vf->BitsPerSample)
			{
			case 8:
				FFDecoderContext->sample_fmt = AV_SAMPLE_FMT_U8;
			case 16:
				FFDecoderContext->sample_fmt = AV_SAMPLE_FMT_S16;
			}
			

			int err = avcodec_open2(FFDecoderContext, FFDecoder, NULL);
			if(err < 0){ //if we failed to open, return error.
				retval = CODEC_FAILED_TO_OPEN;
			}
		}
	}
	catch(...)
	{
		retval = CODEC_UNEXPECTED;
	}

	return retval;
}

Codec_Errors G7231AudioDecoder::Close(){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		if(FFDecoderContext != NULL){ //if we have instantiated the context, then close the codec and free it.
			avcodec_close(FFDecoderContext);
			av_free(FFDecoderContext);
			FFDecoderContext = NULL;
			FFDecoder = NULL;
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}


Codec_Errors G7231AudioDecoder::Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_NOT_SUPPORTED;
	try{
		
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

Codec_Errors G7231AudioDecoder::Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		if(FFDecoder == NULL)
			retval = CODEC_CODEC_NOT_OPENED;
		else if(FFDecoderContext == NULL)
			retval = CODEC_CODEC_NOT_OPENED;
		else if(CurrentFormat == NULL)
			retval = CODEC_CODEC_NOT_OPENED;
		else if(CurrentData == NULL)
			retval = CODEC_CODEC_NOT_OPENED;
		else{
			AVPacket pack;
			av_init_packet(&pack);
			pack.data = (unsigned char*)inSample;
			pack.size = insize;
			AVFrame* frame = av_frame_alloc();
			//avcodec_get_frame_defaults(frame);
			int got_it = 1;
			int ret = avcodec_decode_audio4(FFDecoderContext, frame, &got_it, &pack);
			if(ret < 0)
			{
				retval = CODEC_INVALID_INPUT;
			}
			else if(got_it > 0){
				
				*outsize = frame->linesize[0];
                                *outSample =  frame->data[0];
			}
			else{
				retval = CODEC_NO_OUTPUT;
			}
                        //av_free(frame->data);
			av_frame_free(&frame);
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

G7231AudioDecoder::~G7231AudioDecoder(){
	//Close(); //free the objects by calling close.
}

/////////////////////////////////////////////////////////////
// H264VideoDecoder implementation
/////////////////////////////////////////////////////////////
extern AVCodecParser ff_h264_parser;

H264VideoDecoder::H264VideoDecoder(){
	//intialize all global variables to null for validation checking later.
	FFEncoder = NULL;
	FFEncoderContext = NULL;

	FFDecoder = NULL;
	FFDecoderContext = NULL;

	CurrentFormat = NULL;
	CurrentData = NULL;
	TempFrame = NULL;
	ScaleContext = NULL;
}

Codec_Errors H264VideoDecoder::Open(MediaFormat* encFormat, CodecData* encData){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try
	{
		avcodec_register_all(); //initialize FFMPEG codecs.
		av_register_codec_parser(&ff_h264_parser);
		av_log_set_callback(&avlog_cb);
		sprintf(dbg_buffer, "Opening H.264 Decoder\n");
		DbgOut(dbg_buffer);
		//set global variables.
		CurrentFormat = encFormat;
		CurrentData = encData;
		VideoMediaFormat* vf = (VideoMediaFormat*)encFormat;
		//find the H.264 decoder.
		FFDecoder = avcodec_find_decoder(AV_CODEC_ID_H264);
		if(!FFDecoder) {//if it returned null, we didn't find it, exit function.
			retval = CODEC_NOT_SUPPORTED;
			sprintf(dbg_buffer, "Could not find H.264 Decoder\n");
			DbgOut(dbg_buffer);
		}
		else{ //found decoder, now open.
			//allocate context.
			FFDecoderContext = avcodec_alloc_context3(FFDecoder);
			if(FFDecoderContext == NULL){
				sprintf(dbg_buffer, "Could not allocate H.264 Decoder Context\n");
				DbgOut(dbg_buffer);
			}
			//open decoder.
			int err = avcodec_open2(FFDecoderContext, FFDecoder, NULL);
			if(err < 0) //if error in open, fail.
			{
				retval = CODEC_FAILED_TO_OPEN;
				sprintf(dbg_buffer, "Could not open H.264 Decoder Context\n");
				DbgOut(dbg_buffer);
			}
			else{
				AVRational fps;
				fps.den = vf->FPS;
				fps.num = 1;
				FFDecoderContext->framerate = fps;
				FFDecoderContext->width = vf->Width;
				FFDecoderContext->height = vf->Height;
				FFDecoderContext->coded_width = vf->Width;
				FFDecoderContext->coded_height = vf->Height;
				FFDecoderContext->codec_type = AVMEDIA_TYPE_VIDEO;
				FFDecoderContext->bit_rate = ((double)encData->BitRate/8) / (double)vf->FPS;
				Parser = av_parser_init(AV_CODEC_ID_H264);
				
				if(Parser == NULL){
					sprintf(dbg_buffer, "Parser did not open\n");
					DbgOut(dbg_buffer);
				}
				else{
					sprintf(dbg_buffer, "Got parser\n");
					DbgOut(dbg_buffer);
				}
				//get the ffmpeg format from the desired output format.
				AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
				TempFrame = alloc_picture(fmt, vf->Width, vf->Height); //allocate temp based on this format.

				if(fmt != AV_PIX_FMT_YUV420P) //if it isn't the standard format, then instantiate the scaler.
				{
				
					ScaleContext = sws_getContext(vf->Width, vf->Height,
													 AV_PIX_FMT_YUV420P,
													 vf->Width, vf->Height,
													 fmt,
													 SWS_BICUBIC, NULL, NULL, NULL);
				}
			}
			
		}
	}
	catch(...)
	{
		retval = CODEC_UNEXPECTED;
	}

	return retval;
}

Codec_Errors H264VideoDecoder::Close(){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		sprintf(dbg_buffer, "Closing H264VideoDecoder\n");
		DbgOut(dbg_buffer);
		if(FFDecoderContext != NULL){ //if we have instantiated the context, then close the codec and free it.
			sprintf(dbg_buffer, "\tClosing H264VideoDecoder Codec Context\n");
			DbgOut(dbg_buffer);
			avcodec_close(FFDecoderContext);
			av_parser_close(Parser);
			av_free(Parser);
			av_free(FFDecoderContext);
			FFDecoderContext = NULL;
			FFDecoder = NULL;
		}
		if(ScaleContext != NULL){ //if we have instantiated the scaler, then delete the reference.
			sprintf(dbg_buffer, "\tClosing H264VideoDecoder Scaler\n");
			DbgOut(dbg_buffer);
			av_free(ScaleContext);
			ScaleContext = NULL;
		}

		if(TempFrame != NULL){//free the temp frame used by the scaler.
			//if(TempFrame->data[0] != NULL) av_free(TempFrame->data[0]);
			sprintf(dbg_buffer, "\tClosing H264VideoDecoder Temp Frame\n");
			DbgOut(dbg_buffer);
			av_free(TempFrame);
			TempFrame = NULL;
		}
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	sprintf(dbg_buffer, "Closed H264VideoDecoder\n");
	DbgOut(dbg_buffer);
	return retval;
}


Codec_Errors H264VideoDecoder::Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_NOT_SUPPORTED;
	try{

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

Codec_Errors H264VideoDecoder::Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp){
	Codec_Errors retval = CODEC_SUCCEEDED;
	try{
		VideoMediaFormat* vf = (VideoMediaFormat*)CurrentFormat;
		//validate parameters, if not opened, then fail.
		if(vf == NULL){
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else if(FFDecoderContext == NULL){
			retval = CODEC_CODEC_NOT_OPENED;
		}
		else{
			//initialize a packet.
			AVPacket avpkt;
			av_init_packet(&avpkt);
			avpkt.size = insize;
			avpkt.data = (unsigned char*) inSample;
			//allocate a picture to receive the decoded frame.
			AVFrame* picture= av_frame_alloc();
			int got_picture, len;
			//decode the packet.
			len = avcodec_decode_video2(FFDecoderContext, picture, &got_picture, &avpkt);
			//if got_picture returned true, then we have a decoded frame!
			if(got_picture != 0){
				//get the desired output format.
				AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat);
				//if the desired format isn't the decoder format, then we need to scale.
				if(fmt != AV_PIX_FMT_YUV420P){
					//allocate a frame of the desired format.
					AVFrame* tpic = alloc_picture(fmt, vf->Width, vf->Height);
					//scale the frame.
					sws_scale(ScaleContext, picture->data, picture->linesize,
						  0, vf->Height, tpic->data, tpic->linesize);
					//set the outgoing reference.
					*outSample = tpic->data[0];
					//calculate and set the outgoing frame size, in bytes.
					*outsize = picture->width * picture->height * VideoMediaFormat::GetPixelBits(vf->PixelFormat) / 8;
					//free the temporary picture.
					av_free(tpic);
					tpic = NULL;
				}
				else{//if we desire the standard format, then just set the reference and size.
					*outSample = picture->data[0];
					*outsize = picture->width * picture->height * 12 / 8;
				}
			
			}
			else{
				*outsize = 0;
				retval = Codec_Errors::CODEC_NO_OUTPUT;
			}
			av_free(picture);
		}
		

	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

Codec_Errors H264VideoDecoder::Parse(uint8_t* inSample, long insize, uint8_t** outSample, int* outsize, uint64_t timestamp){
	Codec_Errors retval = Codec_Errors::CODEC_SUCCEEDED;
	try{
		// sprintf(dbg_buffer, "Parsing data of size %d\n", insize);
		// DbgOut(dbg_buffer);
		if(inSample == NULL){
			sprintf(dbg_buffer, "inSample is null!\n");
			DbgOut(dbg_buffer);
			retval = Codec_Errors::CODEC_INVALID_INPUT;
		}
		else if(outSample == NULL){
			sprintf(dbg_buffer, "outSample is null!\n");
			DbgOut(dbg_buffer);
			retval = Codec_Errors::CODEC_INVALID_INPUT;
		}
		else if(Parser == NULL){
			sprintf(dbg_buffer, "Parser is null!\n");
			DbgOut(dbg_buffer);
			retval = Codec_Errors::CODEC_CODEC_NOT_OPENED;
		}
		else if(FFDecoderContext == NULL){
			sprintf(dbg_buffer, "Context is null!\n");
			DbgOut(dbg_buffer);
			retval = Codec_Errors::CODEC_CODEC_NOT_OPENED;
		}
		else{
			int len = av_parser_parse2(Parser, this->FFDecoderContext, outSample, outsize, inSample, insize,0,timestamp,AV_NOPTS_VALUE);
			// sprintf(dbg_buffer, "Parser returned length %d\n", len);
			// DbgOut(dbg_buffer);
			// sprintf(dbg_buffer, "Parser returned size %d\n", *outsize);
			// DbgOut(dbg_buffer);
			
			// if(len == insize && *outsize == 0){
			// 	sprintf(dbg_buffer, "Reparsing.\n");
			// 	DbgOut(dbg_buffer);
			// 	len = av_parser_parse2(Parser, this->FFDecoderContext, outSample, outsize, inSample, insize,0,timestamp,AV_NOPTS_VALUE);
			// }
			
			if(*outsize == 0){
				retval = Codec_Errors::CODEC_NO_OUTPUT;
			}
			else{
				sprintf(dbg_buffer, "Parsed a frame of size %d\n", *outsize);
				DbgOut(dbg_buffer);
			}
		}
		
	}
	catch(...){
		retval = CODEC_UNEXPECTED;
	}
	return retval;
}

H264VideoDecoder::~H264VideoDecoder(){
	
}