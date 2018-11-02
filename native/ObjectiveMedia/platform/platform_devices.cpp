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
using namespace std;
//#ifndef __JS__
#include "platform_devices.h"
#include <stdio.h>
#include <dirent.h>
#include <errno.h>
#include <iostream>
#include <sstream>
#include <stdlib.h>

#ifndef __MINGW32__
#include <time.h>
#include <pthread.h>
#else
#include <windows.h>
#endif


#include <assert.h>

#include <getopt.h>             /* getopt_long() */

#include <fcntl.h>              /* low-level i/o */
#include <unistd.h>
#include <errno.h>
#ifndef __MINGW32__
#include <sys/time.h>
#endif
#ifdef __linux__
#include <malloc.h>

#include <sys/stat.h>
#include <sys/types.h>

#include <sys/mman.h>
#include <sys/ioctl.h>
#endif

#ifndef __ANDROID__
#ifdef __linux__
#include <sys/soundcard.h>
#endif
#else
#include <android/log.h>
#define APPNAME "com.mti.primitives.devices"
#endif
#ifdef __linux__
#include <asm/types.h>          /* for videodev2.h */

//#include <linux/videodev2.h>
#endif
#ifdef __MINGW32__
DWORD WINAPI VideoInputDevice_Thread( LPVOID lpParam );
#endif
/********************************************
OS Specific Structures and functions
********************************************/

typedef struct StandardVideoFormat{
    int Width;
    int Height;
    int pixelFormat;
}StandardVideoFormat;

typedef struct StandardAudioFormat{
    int SampleRate;
    int BitsPerSample;
    int Channels;
};

typedef struct VideoInputBuffer{
    void* Buffer;
    int Length;
}VideoInputBuffer;

typedef struct VideoInputDeviceContext{
    void* DeviceHandle;
    long ImageSize;
    VideoMediaFormat* Format;
    VideoMediaFormat* NativeFormat;
    #ifndef __MINGW32__
    pthread_t CaptureThread;
    #else
    HANDLE CaptureThread;
    #endif
    DeviceListener* Listener;
    bool Stopped;
    VideoInputBuffer* Buffers;
    unsigned int BufferCount;
    AVFrame* TempFrame;
    SwsContext* ScaleContext;
    AVCodecContext* CodecContext;
    AVCodec* Codec;
    VideoInputDeviceContext(){
        DeviceHandle = NULL;
        ImageSize = 0;
        Format = NULL;

        #ifndef __MINGW32__

        CaptureThread = (pthread_t)-1;
        #else
        CaptureThread = NULL;
        #endif
        Listener = NULL;
        Stopped = false;
        //Buffers = NULL;
        //BufferCount = 0;
        TempFrame = NULL;
        ScaleContext = NULL;
        CodecContext = NULL;
        Codec = NULL;
    };
    ~VideoInputDeviceContext(){
        if(TempFrame != NULL){
            if(TempFrame->data[0] != NULL)
                av_free(TempFrame->data[0]);
            av_free(TempFrame);
        }
        TempFrame = NULL;
        if(ScaleContext != NULL){
            av_free(ScaleContext);
        }
    }
}VideoInputDeviceContext;

typedef struct AudioInputDeviceContext{
    int DeviceHandle;
    AudioMediaFormat* Format;
    #ifndef __JS__
    #ifndef __MINGW32__
    pthread_t CaptureThread;
    #else
    HANDLE CaptureThread;
    #endif
    #else
    void* CaptureThread;
    #endif
    DeviceListener* Listener;
    bool Stopped;
    
    AudioInputDeviceContext(){
        DeviceHandle = -1;
        Format = NULL;
        #ifndef __JS__
        #ifndef __MINGW32__
           CaptureThread = (pthread_t)-1;
        #else
            CaptureThread = NULL;
        #endif
        #else
            CaptureThread = NULL;
        #endif
        Listener = NULL;
        Stopped = false;
        
    }
    ~AudioInputDeviceContext(){
        
    }
}AudioInputDeviceContext;

#define StandardFormatCount 3
StandardVideoFormat StandardFormats[] = 
{
    /*
        RGB32=	31, //32 bit
	ARGB32=	32, //32 bit
	AYUV=	65, //32 bit
	UYVY=	66, //16 bit
	Y411=	67, //12 bit
	Y41P=	68, //12 bit
	Y211=	69, //8 bit
	YUY2=	70, //16 bit
	YVYU=	71, //16 bit
	YUYV=	72, //16 bit
	IF09=	73, //9.5 bits
	IYUV=	74, //12 bits
	YV12=	75, //12 bits
	YVU9=	76, //9 buts
	I420=	77, //12 bits
     */
    {160,120,RGB24},
    {320,240,RGB24},
    {640,480,RGB24}
};
#define StandardAudioFormatCount 4
StandardAudioFormat StandardAudioFormats[] = {
    {8000, 8, 1},
    {8000, 16, 1},
    {11025, 8, 1},
    {11025, 16, 1}
};


int GetPixelByteSize(VideoPixelFormat fmt){
    int retval = 3;
    switch(fmt){
        case RGB24:
            retval = 3;
            break;
        case IYUV:
            retval = 2;
            break;
        case YUYV:
            retval = 2;
            break;
        case RGB565:
            retval = 2;
            break;
        case RGB555:
            retval = 2;
            break;
        default:
            retval = 2;
    }
    return retval;
}

long GetImageSize(VideoMediaFormat* format){
    return format->Width * format->Height * GetPixelByteSize(format->PixelFormat);
}



typedef struct VideoOutputDeviceContext{
	
}VideoOutputDeviceContext;

typedef struct AudioOutputDeviceContext{
	
}AudioOutputDeviceContext;



/********************************************
VideoMediaFormat Implementation
********************************************/
VideoMediaFormat::VideoMediaFormat(){

}

VideoMediaFormat::~VideoMediaFormat(){

}

/********************************************
AudioMediaFormat Implementation
********************************************/
AudioMediaFormat::AudioMediaFormat(){

}

AudioMediaFormat::~AudioMediaFormat(){

}

/********************************************
VideoInputDevice Implementation
********************************************/
VideoInputDevice::VideoInputDevice(){
        
    av_register_all();
    avdevice_register_all();
    avformat_network_init();
    avcodec_register_all();
	this->DeviceName = "";
	this->DeviceIndex = 0;
	this->Listener = NULL;
	this->DeviceContext = NULL;
	FormatCount = 0;
}

 #ifndef __MINGW32__
 void *VideoInputDevice_Thread(void* ptr){
 #else
 DWORD WINAPI VideoInputDevice_Thread(LPVOID ptr){
 #endif
    
#ifndef __JS__                
    VideoInputDeviceContext* context = (VideoInputDeviceContext*) ptr;
    av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread++\n");
    if(context->Format->FPS <= 0) context->Format->FPS = 20;
    if(context->Format->FPS % 2 > 0){
        context->Format->FPS++;
    }
    double adjfps = context->Format->FPS;
    
    long sleepTime = ((double) 1000/adjfps)/2;//33000;
    //float clockAdjust = ((float)33.333)/((float)CLOCKS_PER_SEC);
    long long StartTicks = 0;
    //long long lastTicks = 0;
    long long timestamp = 0;
    long cycleCount = 0;
    av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread starting control loop\n");
    AVFrame* sourceFrame = av_frame_alloc();
    while(!context->Stopped){
        
        if (context->DeviceHandle != NULL) {
            if(context->Listener != NULL)
            {
                void* buffer = NULL;
                int bufsize = 0;
                //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread allocating new packet.\n");
                AVPacket *packet=(AVPacket *)av_malloc(sizeof(AVPacket));
                //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread reading packet\n");
                if(av_read_frame((AVFormatContext*) context->DeviceHandle, packet) >= 0){
                    buffer = NULL;
                    bufsize = 0;
                    #ifndef __MINGW32__
                    
//                    if(StartTicks == 0){
//                        StartTicks = clock() * clockAdjust;
//                        av_log(context->DeviceHandle, AV_LOG_INFO, "Starting tick is %d\n", StartTicks);
//                    }
                    timestamp = cycleCount * sleepTime;//(clock() * clockAdjust) - StartTicks;
                    
                    #else
                    if(StartTicks == 0){
                        StartTicks = GetTickCount();
                    }
                    timestamp = GetTickCount() - StartTicks;
                    #endif

                    if(context->ScaleContext != NULL && context->CodecContext != NULL && cycleCount % 2 == 0){
                        VideoMediaFormat* native = context->NativeFormat;
                        VideoMediaFormat* adjusted = context->Format;
                        //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread getting source frame\n");
                        //AVFrame* source = alloc_and_fill_picture((AVPixelFormat)VideoMediaFormat::GetFFPixel(native->PixelFormat), native->Width, native->Height, packet->data);
                        int goahead = 1;
                        if(context->CodecContext->codec_id != AV_CODEC_ID_RAWVIDEO){
                            //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread need to decode.\n");
                            int got_picture;
                            if(avcodec_decode_video2(context->CodecContext, sourceFrame, &got_picture, packet)){
                                if(!got_picture){
                                    goahead = 0;
                                }
                            }
                        }
                        else{
                             if(avpicture_fill((AVPicture*) sourceFrame, packet->data, (AVPixelFormat)VideoMediaFormat::GetFFPixel(native->PixelFormat), native->Width, native->Height) < 0){
                                 goahead = 0;
                             }
                        }
                        if(goahead == 1){
                            if(context->NativeFormat->PixelFormat != context->Format->PixelFormat || context->NativeFormat->Width != context->Format->Width){
                                
                                //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread scaling to desired format\n");
                                
                                int outheight = sws_scale(context->ScaleContext, sourceFrame->data, sourceFrame->linesize,0, native->Height, context->TempFrame->data, context->TempFrame->linesize);
                                //set the outgoing reference.
                                if(outheight > 0)
                                {
                                    //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread got my new scaled buffer of height %d\n", outheight);
                                    buffer = context->TempFrame->data[0];
                                    
                                        //calculate and set the outgoing frame size, in bytes.
                                    bufsize = adjusted->Width * adjusted->Height * VideoMediaFormat::GetPixelBits(RGB24) / 8;
                                }
                            }
                            else{
                                buffer = sourceFrame->data[0];
                                bufsize = packet->size;
                            }
                            
                        }
                    }
                    //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread freeing packet.\n");
                    
                }
                
                //av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread passing up buffer\n");
                if(buffer != NULL) context->Listener->SampleCaptured(NULL, buffer, bufsize, timestamp);
                av_free_packet(packet);
                //if(sourceFrame != NULL) av_free(sourceFrame);
            }
            //ioctl (context->DeviceHandle, VIDIOC_QBUF, &buf);
        }
        cycleCount++;
        #ifndef __MINGW32__
        
        usleep(sleepTime * 1000);
        #else
        Sleep(sleepTime);
        #endif
    }
    av_log(context->DeviceHandle, AV_LOG_INFO, "VideoInputDevice_Thread--\n");
   #ifndef __MINGW32__
    pthread_exit(NULL);
    #else
        ExitThread(0);
    #endif
#endif
}

Device_Errors VideoInputDevice::Open(MediaFormat* format){
    Device_Errors retval = SUCCEEDED;
#ifndef __JS__
    try
    {
        VideoMediaFormat* vformat = (VideoMediaFormat*)format;
        VideoInputDeviceContext* context = new VideoInputDeviceContext();
        
        
        context->DeviceHandle = NULL;
        
        char index[100];
#ifdef __linux__
        AVInputFormat *iformat = av_find_input_format("v4l2");
        
        sprintf(index,"/dev/video%d", DeviceIndex);
#endif
#ifdef __APPLE__
        AVInputFormat *iformat = av_find_input_format("avfoundation");
        sprintf(index,"%d", DeviceIndex);
#endif
#ifdef __MINGW32__
        AVInputFormat *iformat = av_find_input_format("dshow");
        sprintf(index,"video=%s", DeviceName.c_str());

#endif
        AVDictionary *options = NULL;
        if(vformat->FPS <= 0){
            vformat->FPS = 20;
        }
        char framerate[20];
        char video_size[40];
        char pixfmt[20];
        //char rtbufsize[40];
        sprintf(framerate, "%d:1", vformat->FPS);
        
        sprintf(video_size, "%dx%d", vformat->Width, vformat->Height);
        int ffpix = VideoMediaFormat::GetFFPixel(vformat->PixelFormat);
        sprintf(pixfmt, "%s", VideoMediaFormat::GetFFPixelName(ffpix));
        //sprintf(rtbufsize, "%d", vformat->FPS * vformat->Width * vformat->Height * 3);
        
        
        #ifdef __APPLE__
        av_dict_set(&options, "frame_rate", framerate, 0);
        av_log(context->DeviceHandle, AV_LOG_INFO, "Setting framerate to %s\n", framerate);
#else
        
        
        av_dict_set(&options, "video_size", video_size, 0);
        av_log(context->DeviceHandle, AV_LOG_INFO, "Setting video size to %s\n", video_size);
        av_dict_set(&options, "framerate", framerate, 0);
        av_log(context->DeviceHandle, AV_LOG_INFO, "Setting framerate to %s\n", framerate);
        //av_dict_set(&options, "pixel_format", pixfmt, 0);
        //av_log(context->DeviceHandle, AV_LOG_INFO, "Setting pixel format to %s\n", pixfmt);
#endif
        //av_dict_set(&options, "rtbufsize", rtbufsize, 0);
        //av_dict_set(&options, "pixel_format", pixfmt, 0);
        //printf("Setting pixel format to %s\n", pixfmt);
        int error = avformat_open_input((AVFormatContext**)&context->DeviceHandle, index, iformat, &options);
        if(error == -5){
            vformat->FPS = 30;
            sprintf(framerate, "%d:1", vformat->FPS);
        
            av_dict_set(&options, "framerate", framerate, 0);
            av_log(context->DeviceHandle, AV_LOG_INFO, "Trying framerate to %s\n", framerate);
            error = avformat_open_input((AVFormatContext**)&context->DeviceHandle, index, iformat, &options);
        }
        if(error != 0)
        {
            av_log(context->DeviceHandle, AV_LOG_INFO, "Error opening device = %d\n", error);
            char errormsg[1024];
            av_strerror(error, errormsg, 1024);
            av_log(context->DeviceHandle, AV_LOG_INFO, "%s\n", errormsg);
            retval = INVALID_DEVICE;
        }
        else{
            context->Listener = Listener;
            av_log(context->DeviceHandle, AV_LOG_INFO, "Adding device listener to context\n");
            DeviceContext = context;
            context->Stopped = false;
            context->CodecContext = ((AVFormatContext*)context->DeviceHandle)->streams[0]->codec;
            context->Codec = avcodec_find_decoder(context->CodecContext->codec_id);
            if(context->CodecContext != NULL && context->Codec != NULL){
                av_log(context->DeviceHandle, AV_LOG_INFO, "Found decoder for %i\n", context->CodecContext->codec_id);
                error = 0;
                if(context->CodecContext->codec_id != AV_CODEC_ID_RAWVIDEO){
                    context->CodecContext->pix_fmt = AV_PIX_FMT_YUV420P;
                    error = avcodec_open2(context->CodecContext, context->Codec, NULL);
                }
                
                if(error != 0){
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Error opening codec = %d\n", error);
                    char errormsg[1024];
                    av_strerror(error, errormsg, 1024);
                    av_log(context->DeviceHandle, AV_LOG_INFO, "%s\n", errormsg);
                    context->CodecContext = NULL;
                    avcodec_close(context->CodecContext);
                    context->Codec = NULL;
                    retval = INVALID_FORMAT;
                    avformat_close_input((AVFormatContext**)&context->DeviceHandle);
                }
                else{
                    
                    AVPixelFormat fmt = (AVPixelFormat)VideoMediaFormat::GetFFPixel(RGB24);
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Allocating temp scaling frame\n");
                    context->TempFrame = alloc_picture(fmt, vformat->Width, vformat->Height); //allocate temp based on this format.
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Codec Pixel Format is %d->%s\n", context->CodecContext->pix_fmt, VideoMediaFormat::GetFFPixelName(context->CodecContext->pix_fmt));
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Initiating scaling context\n");
                    
                    context->ScaleContext = sws_getContext(context->CodecContext->width, context->CodecContext->height,context->CodecContext->pix_fmt, vformat->Width, vformat->Height,fmt,SWS_BICUBIC, NULL, NULL, NULL);
                    context->NativeFormat = new VideoMediaFormat();
                    context->NativeFormat->PixelFormat = VideoMediaFormat::FromFFPixel(context->CodecContext->pix_fmt);
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Native Pixel Format is %i\n", context->NativeFormat->PixelFormat);
                    context->NativeFormat->Width = context->CodecContext->width;
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Native Width is %i\n", context->NativeFormat->Width);
                    context->NativeFormat->Height = context->CodecContext->height;
                    av_log(context->DeviceHandle, AV_LOG_INFO, "Native Height is %i\n", context->NativeFormat->Height);
                    
                    vformat->PixelFormat = RGB24;
                    context->Format = vformat;
                    #ifndef __MINGW32__            
                    int r = pthread_create( &context->CaptureThread, NULL, &VideoInputDevice_Thread, (void*) DeviceContext);
                    if(r != 0){
                        retval = NOT_SUPPORTED;
                    }
                    #else

                    av_log(context->DeviceHandle, AV_LOG_INFO, "Starting thread\n");
                    context->CaptureThread = CreateThread(NULL, 0,VideoInputDevice_Thread, (void*) DeviceContext, 0, NULL);
                    if(context->CaptureThread == NULL){
                        retval = NOT_SUPPORTED;
                    }
                    else{
                        av_log(context->DeviceHandle, AV_LOG_INFO, "Starting W32 thread.\n");
                    }
                    #endif
                }
            }
            else{
                av_log(context->DeviceHandle, AV_LOG_INFO, "Unable to find the decoder for the codec.\n");
            }
            
            
        }
        av_dict_free(&options);
            
    
            
        
        if(retval != SUCCEEDED){
            Close();
        }

    }
    catch(...){
        retval = UNEXPECTED;
    }
#endif
    return retval;
}

Device_Errors VideoInputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try
	{
            if(DeviceContext != NULL)
            {
                
                VideoInputDeviceContext* context = (VideoInputDeviceContext*)DeviceContext;
                context->Stopped = true;
                av_log(context->DeviceHandle, AV_LOG_INFO, "Signaling the thread to stop.\n");
                #ifndef __MINGW32__
                pthread_join(context->CaptureThread, NULL);
                #else
                WaitForSingleObject(context->CaptureThread, INFINITE);
                CloseHandle(context->CaptureThread);
                #endif
                av_log(context->DeviceHandle, AV_LOG_INFO, "Freeing the scale context.\n");
                if(context->ScaleContext != NULL) sws_freeContext(context->ScaleContext);
                av_log(context->DeviceHandle, AV_LOG_INFO, "Freeing the codec context.\n");
                if(context->CodecContext != NULL) avcodec_close(context->CodecContext);
                av_log(context->DeviceHandle, AV_LOG_INFO, "Closing the device context.\n");
                avformat_close_input((AVFormatContext**)&context->DeviceHandle);

                //delete(context);
                //DeviceContext = NULL;
            }
            SAFEDELETE(DeviceContext);
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors VideoInputDevice::GetDevices(std::vector<Device*> &deviceList){
    Device_Errors retval = SUCCEEDED;
#ifndef __JS__
    try{
        int error = 0;
        AVFormatContext *pFormatCtx = NULL;
        char devnum[100];
        
        for(int x = 0; x < 16; x++){
            printf("Trying device at %d\n", x);
            
            
#ifdef __linux__
            sprintf(devnum, "/dev/video%d", x);
            AVInputFormat *iformat = av_find_input_format("v4l2");
    
#endif
#ifdef __APPLE__
            sprintf(devnum, "%d", x);
            AVInputFormat *iformat = av_find_input_format("avfoundation");
#endif
#ifdef __MINGW32__
            
            sprintf(devnum, "video=%d", x);
            AVInputFormat *iformat = av_find_input_format("dshow");
    
#endif
            printf("Device number is %s\n", devnum);
            
            error = avformat_open_input(&pFormatCtx, devnum, iformat, NULL);
            if(error == 0){
                
                printf("Getting details for input %d\n", x);
                VideoInputDevice* vid = new VideoInputDevice();
                vid->DeviceIndex = x;
                char devname[1024];
                #ifdef __MINGW32__
                sprintf(devname, "%s", pFormatCtx->filename);
                #else
                sprintf(devname, "video%d", x);
                #endif
                string name(devname);
                vid->DeviceName = name;
                printf("Device has %d streams\n", (int)pFormatCtx->nb_streams);
#ifndef __APPLE__
                avformat_close_input(&pFormatCtx);
                for(int i = 0; i < StandardFormatCount; i++){
                    
                    AVDictionary *options = NULL;

                    char video_size[40];
                    char pixfmt[20];
                    sprintf(video_size, "%dx%d", StandardFormats[i].Width, StandardFormats[i].Height);
                    int ffpix = VideoMediaFormat::GetFFPixel((VideoPixelFormat)StandardFormats[i].pixelFormat);
                    sprintf(pixfmt, "%s", VideoMediaFormat::GetFFPixelName(ffpix));
                    av_log(pFormatCtx, AV_LOG_INFO, "Checking video size %s and FF format %s and our format is %i\n", video_size, pixfmt, StandardFormats[i].pixelFormat);
                    av_dict_set(&options, "video_size", video_size, 0);
                    av_dict_set(&options, "pixel_format", pixfmt, 0);
                    if(avformat_open_input(&pFormatCtx, devnum, iformat, &options) == 0){
                        if(pFormatCtx->nb_streams > 0){
                            VideoMediaFormat* vf = new VideoMediaFormat();
                            vf->Width = pFormatCtx->streams[0]->codec->width;
                            printf("Stream %d width = %d\n", i, vf->Width);
                            vf->Height = pFormatCtx->streams[0]->codec->height;
                            printf("Stream %d height = %d\n", i, vf->Height);
                            vf->PixelFormat = (VideoPixelFormat)StandardFormats[i].pixelFormat;
                            printf("Stream %d Pixel = %d\n", i, vf->PixelFormat);
                            vf->FPS = 0;

                            vid->Formats.push_back(vf);
                            printf("Stream %d pushed to format list\n", i);
                            vid->FormatCount = vid->Formats.size();
                        }
                        avformat_close_input(&pFormatCtx);
                    }
                }
#else
                for(int i=0; i < pFormatCtx->nb_streams; i++) {
                    printf("Stream %d has a name of %s\n", i, pFormatCtx->streams[i]->codec->codec_name);
                    if(pFormatCtx->streams[i]->codec->codec_type==AVMEDIA_TYPE_VIDEO)
                    {
                        printf("Stream %d has is video\n", i);
                        VideoMediaFormat* vf = new VideoMediaFormat();
                        vf->Width = pFormatCtx->streams[i]->codec->width;
                        printf("Stream %d width = %d\n", i, vf->Width);
                        vf->Height = pFormatCtx->streams[i]->codec->height;
                        printf("Stream %d height = %d\n", i, vf->Height);
                        vf->PixelFormat = VideoMediaFormat::FromFFPixel(pFormatCtx->streams[i]->codec->pix_fmt);
                        vf->FPS = 0;
                        printf("Stream %d FFPixel = %d\n", i, pFormatCtx->streams[i]->codec->pix_fmt);
                        printf("Stream %d Pixel = %d\n", i, vf->PixelFormat);
                        printf("Stream %d FPS = %d\n", i, vf->FPS);
                        vid->Formats.push_back(vf);
                        printf("Stream %d pushed to format list\n", i);
                        vid->FormatCount = vid->Formats.size();
                    }
                    
                    
                }
#endif
                deviceList.push_back(vid);
                printf("Device %d pushed to device list\n", x);
#ifdef __APPLE__
                avformat_close_input(&pFormatCtx);
#endif
                printf("Closed Context\n");
                //avformat_free_context(pFormatCtx);
                pFormatCtx = NULL;
            }
            else{
                break;
            }
                
                
        }
        
    }
    catch(...){
        
    }
#endif
    return retval;
}

VideoInputDevice::~VideoInputDevice(){
	Close();
	for(int x=0; x < FormatCount; x++)
	{
		if(Formats[x] != NULL)
		{
                    delete(Formats[x]);
                    Formats[x] = NULL;
		}
	}
	Formats.clear();
}

/********************************************
AudioInputDevice Implementation
*********************************************/

AudioInputDevice::AudioInputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
}

Device_Errors AudioInputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try
	{
		Close();
		AudioInputDeviceContext* context = new AudioInputDeviceContext();
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors AudioInputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try
	{
		if(DeviceContext != NULL)
		{
			AudioInputDeviceContext* context = (AudioInputDeviceContext*)DeviceContext;
			
			
		}
		SAFEDELETE(DeviceContext);
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}

Device_Errors AudioInputDevice::GetDevices(std::vector<Device*> &deviceList){
    Device_Errors retval = SUCCEEDED;
    try{

    }
    catch(...)
    {
        retval = UNEXPECTED;
    }
    return retval;
}

AudioInputDevice::~AudioInputDevice()
{
	Close();
	for(int x=0; x < FormatCount; x++)
	{
		if(Formats[x] != NULL)
		{
				delete(Formats[x]);
				Formats[x] = NULL;
		}
	}
	Formats.clear();
};

/********************************************
VideoOutputDevice Implementation
********************************************/
VideoOutputDevice::VideoOutputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
	//See OutputDevice header.
Device_Errors VideoOutputDevice::Present(void* sample, long size, long long timestamp){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device Header.
Device_Errors VideoOutputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}
	//Opens the output device with a specified surface, width, height and rotation.
Device_Errors VideoOutputDevice::Open(MediaFormat* format, void* surface, int width, int height, bool rotate){
	Device_Errors retval = SUCCEEDED;
	try
	{
		Surface = surface;
		SurfaceWidth = width;
		SurfaceHeight = height;
		RotateFrames = rotate;
		Open(format);
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}

	//See Device Header
Device_Errors VideoOutputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device Header
Device_Errors VideoOutputDevice::GetDevices(std::vector<Device*> &deviceList){
	return NOT_SUPPORTED;
}

VideoOutputDevice::~VideoOutputDevice(){
	Close();
}

/*********************************************
AudioOutputDevice Implementation
*********************************************/
AudioOutputDevice::AudioOutputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
	//See OutputDevice header.
Device_Errors AudioOutputDevice::Present(void* sample, long size, long long timestamp){
	Device_Errors retval = SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)DeviceContext;
		if(DeviceContext == NULL){
			retval = INVALID_DEVICE;
		}
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::Open(MediaFormat* format){
	Device_Errors retval = SUCCEEDED;
	try{
            AudioOutputDeviceContext* context = new AudioOutputDeviceContext();
            AudioMediaFormat* aformat = (AudioMediaFormat*)format;
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::Close(){
	Device_Errors retval = SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)DeviceContext;
		
		SAFEDELETE(DeviceContext);
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::GetDevices(std::vector<Device*> &deviceList){
	Device_Errors retval = SUCCEEDED;
	try{
		
	}
	catch(...)
	{
		retval = UNEXPECTED;
	}
	return retval;
}

AudioOutputDevice::~AudioOutputDevice(){
	Close();
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
//#endif