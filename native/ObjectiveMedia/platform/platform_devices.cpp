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
#ifdef __linux__
#include <malloc.h>

#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
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

#include <linux/videodev2.h>
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
    int PixelFormat;
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
    #ifndef __MINGW32__
    pthread_t CaptureThread;
    #else
    HANDLE CaptureThread;
    #endif
    DeviceListener* Listener;
    bool Stopped;
    
    AudioInputDeviceContext(){
        DeviceHandle = -1;
        Format = NULL;
        #ifndef __MINGW32__
           CaptureThread = (pthread_t)-1;
        #else
            CaptureThread = NULL;
        #endif
        Listener = NULL;
        Stopped = false;
        
    }
    ~AudioInputDeviceContext(){
        
    }
}AudioInputDeviceContext;

#define StandardFormatCount 60
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
    {640,480,RGB24},
    {720,480,RGB24},
    {1024,768,RGB24},
    {160,120,IYUV},
    {320,240,IYUV},
    {640,480,IYUV},
    {720,480,IYUV},
    {1024,768,IYUV},
    {160,120,YUYV},
    {320,240,YUYV},
    {640,480,YUYV},
    {720,480,YUYV},
    {1024,768,YUYV},
    {160,120,RGB565},
    {320,240,RGB565},
    {640,480,RGB565},
    {720,480,RGB565},
    {1024,768,RGB565},
    {160,120,RGB555},
    {320,240,RGB555},
    {640,480,RGB555},
    {720,480,RGB555},
    {1024,768,RGB555},
    {160,120,RGB32},
    {320,240,RGB32},
    {640,480,RGB32},
    {720,480,RGB32},
    {1024,768,RGB32},
    {160,120,ARGB32},
    {320,240,ARGB32},
    {640,480,ARGB32},
    {720,480,ARGB32},
    {1024,768,ARGB32},
    {160,120,AYUV},
    {320,240,AYUV},
    {640,480,AYUV},
    {720,480,AYUV},
    {1024,768,AYUV},
    {160,120,UYVY},
    {320,240,UYVY},
    {640,480,UYVY},
    {720,480,UYVY},
    {1024,768,UYVY},
    {160,120,Y411},
    {320,240,Y411},
    {640,480,Y411},
    {720,480,Y411},
    {1024,768,Y411},
    {160,120,YUY2},
    {320,240,YUY2},
    {640,480,YUY2},
    {720,480,YUY2},
    {1024,768,YUY2},
    {160,120,YV12},
    {320,240,YV12},
    {640,480,YV12},
    {720,480,YV12},
    {1024,768,YV12},
    {160,120,UNKNOWN},
    {320,240,UNKNOWN},
    {640,480,UNKNOWN},
    {720,480,UNKNOWN},
    {1024,768,UNKNOWN},
};
#define StandardAudioFormatCount 4
StandardAudioFormat StandardAudioFormats[] = {
    {8000, 8, 1},
    {8000, 16, 1},
    {11025, 8, 1},
    {11025, 16, 1}
};
#ifdef __linux__
__u32 GetBPPFCC(VideoPixelFormat fmt){
    __u32 retval = V4L2_PIX_FMT_BGR24;
    switch(fmt){
        case RGB24:
            retval = V4L2_PIX_FMT_BGR24;
            break;
        case IYUV:
            retval = V4L2_PIX_FMT_YUV420;
            break;
        case YUYV:
            retval = V4L2_PIX_FMT_YUYV;
            break;
        case RGB565:
            retval = V4L2_PIX_FMT_RGB565;
            break;
        case RGB555:
            retval = V4L2_PIX_FMT_RGB555;
            break;
        case UYVY:
            retval = V4L2_PIX_FMT_UYVY;
            break;
        case YV12:
            retval = V4L2_PIX_FMT_YUV420;
            break;
#ifndef __ANDROID__
        case UNKNOWN:
            retval = V4L2_PIX_FMT_H264;
            break;
#endif
        default:
            retval = V4L2_PIX_FMT_BGR24;
    }
    return retval;
};
#endif

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
#ifdef __linux__
static int
xioctl                          (int                    fd,
                                 int                    request,
                                 void *                 arg)
{
        int r;

        do r = ioctl (fd, request, arg);
        while (-1 == r && EINTR == errno);

        return r;
}
#endif



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
    VideoInputDeviceContext* context = (VideoInputDeviceContext*) ptr;
    if(context->Format->FPS <= 0) context->Format->FPS = 20;
    double adjfps = context->Format->FPS;
    long sleepTime = 1000000*((double) 1000/adjfps);
    long long StartTicks = 0;
    while(!context->Stopped){
        //v4l2_buffer buf;
        //memset (&buf, 0, sizeof(buf));

        //buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        //buf.memory = V4L2_MEMORY_MMAP;
        
        if (context->DeviceHandle != NULL) {
            if(context->Listener != NULL)
            {
                void* buffer = NULL;
                int bufsize = 0;
                AVPacket *packet=(AVPacket *)av_malloc(sizeof(AVPacket));
                if(av_read_frame((AVFormatContext*) context->DeviceHandle, packet) >= 0){
                    buffer = NULL;
                    bufsize = 0;
                    if(context->ScaleContext != NULL){
                        VideoMediaFormat* native = context->NativeFormat;
                        VideoMediaFormat* adjusted = context->Format;
                        AVFrame* source = alloc_and_fill_picture((AVPixelFormat)VideoMediaFormat::GetFFPixel(native->PixelFormat), native->Width, native->Height, packet->data);
                        if(source != NULL){
                            int outheight = sws_scale(context->ScaleContext, source->data, source->linesize,0, adjusted->Height, context->TempFrame->data, context->TempFrame->linesize);
                            //set the outgoing reference.
                            if(outheight > 0)
                            {
                                buffer = context->TempFrame->data[0];
                                    //calculate and set the outgoing frame size, in bytes.
                                bufsize = adjusted->Width * adjusted->Height * VideoMediaFormat::GetPixelBits(RGB24) / 8;
                            }
                            av_free(source);
                        }
                    }
                    else{
                        buffer = malloc(packet->size);
                        memcpy(buffer, packet->data, packet->size);
                    }
                    av_free_packet(packet);
                }
                #ifndef __MINGW32__
                struct timeval tv;
                struct timezone tz;
                gettimeofday(&tv, &tz);
                if(StartTicks == 0){
                    StartTicks = tv.tv_usec / 1000;
                }
                long long timestamp = (tv.tv_usec/1000) - StartTicks;
                #else
                if(StartTicks == 0){
                    StartTicks = GetTickCount();
                }
                long long timestamp = GetTickCount() - StartTicks;
                #endif
                context->Listener->SampleCaptured(NULL, buffer, bufsize, timestamp);
            }
            //ioctl (context->DeviceHandle, VIDIOC_QBUF, &buf);
        }
        #ifndef __MINGW32__
        
        timespec tv;
        tv.tv_nsec = sleepTime;
        tv.tv_sec = 0;
        nanosleep(&tv, NULL);
        #else
        Sleep(sleepTime/1000000);
        #endif
    }
   #ifndef __MINGW32__
    pthread_exit(NULL);
    #else
        ExitThread(0);
    #endif
}

Device_Errors VideoInputDevice::Open(MediaFormat* format){
    Device_Errors retval = SUCCEEDED;
    try
    {
        VideoMediaFormat* vformat = (VideoMediaFormat*)format;
        VideoInputDeviceContext* context = new VideoInputDeviceContext();
        
        if(vformat->PixelFormat != RGB24){
            for(int x = 0; x < Formats.size(); x++){
                VideoMediaFormat* f = (VideoMediaFormat*)Formats[x];
                if(vformat->PixelFormat == ANY){
                    if(vformat->Width == f->Width && vformat->Height == f->Height){
                        vformat->PixelFormat = f->PixelFormat;
                        PixelFormat fmt = (PixelFormat)VideoMediaFormat::GetFFPixel(RGB24);
                        context->TempFrame = alloc_picture(fmt, vformat->Width, vformat->Height); //allocate temp based on this format.
                        context->ScaleContext = sws_getContext(vformat->Width, vformat->Height,(AVPixelFormat)VideoMediaFormat::GetFFPixel(vformat->PixelFormat), vformat->Width, vformat->Height,fmt,SWS_BICUBIC, NULL, NULL, NULL);
                        context->NativeFormat = f;
                        vformat->PixelFormat = RGB24;
                        context->Format = vformat;
                        break;
                    }
                }
                else{
                    if(vformat->Width == f->Width && vformat->Height == f->Height && vformat->PixelFormat == f->PixelFormat){
                        vformat->PixelFormat = f->PixelFormat;
                        PixelFormat fmt = (PixelFormat)VideoMediaFormat::GetFFPixel(RGB24);
                        context->TempFrame = alloc_picture(fmt, vformat->Width, vformat->Height); //allocate temp based on this format.
                        context->ScaleContext = sws_getContext(vformat->Width, vformat->Height,(AVPixelFormat)VideoMediaFormat::GetFFPixel(vformat->PixelFormat), vformat->Width, vformat->Height,fmt,SWS_BICUBIC, NULL, NULL, NULL);
                        vformat->PixelFormat = RGB24;
                        context->Format = vformat;
                        context->NativeFormat = f;
                        break;
                    }
                }
                
            }
        }
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
        char rtbufsize[40];
        sprintf(framerate, "%d:1", vformat->FPS);
        
        sprintf(video_size, "%dx%d", vformat->Width, vformat->Height);
        
        sprintf(pixfmt, "%d", (AVPixelFormat)VideoMediaFormat::GetFFPixel(vformat->PixelFormat));
        sprintf(rtbufsize, "%d", vformat->FPS * vformat->Width * vformat->Height * 3);
        
        #ifdef __MINGW32__
        av_dict_set(&options, "video_size", video_size, 0);
        printf("Setting video size to %s\n", video_size);
        av_dict_set(&options, "framerate", framerate, 0);
        printf("Setting framerate to %s\n", framerate);
        #endif
        #ifdef __APPLE__
        av_dict_set(&options, "frame_rate", framerate, 0);
        printf("Setting framerate to %s\n", framerate);
        #endif
        av_dict_set(&options, "rtbufsize", rtbufsize, 0);
        //av_dict_set(&options, "pixel_format", pixfmt, 0);
        //printf("Setting pixel format to %s\n", pixfmt);
        int error = avformat_open_input((AVFormatContext**)&context->DeviceHandle, index, iformat, &options);
        if(error == -5){
            vformat->FPS = 30;
            sprintf(framerate, "%d:1", vformat->FPS);
        
            av_dict_set(&options, "framerate", framerate, 0);
            printf("Trying framerate to %s\n", framerate);
            error = avformat_open_input((AVFormatContext**)&context->DeviceHandle, index, iformat, &options);
        }
        if(error != 0)
        {
            printf("Error opening device = %d\n", error);
            char errormsg[1024];
            av_strerror(error, errormsg, 1024);
            printf("%s\n", errormsg);
            retval = INVALID_DEVICE;
        }
        else{
            context->Listener = Listener;
            printf("Adding device listener to context\n");
            DeviceContext = context;
            context->Stopped = false;
            #ifndef __MINGW32__            
            int r = pthread_create( &context->CaptureThread, NULL, &VideoInputDevice_Thread, (void*) DeviceContext);
            if(r != 0){
                retval = NOT_SUPPORTED;
            }
            #else

            printf("Starting thread\n");
            context->CaptureThread = CreateThread(NULL, 0,VideoInputDevice_Thread, (void*) DeviceContext, 0, NULL);
            if(context->CaptureThread == NULL){
                retval = NOT_SUPPORTED;
            }
            else{
                printf("Starting W32 thread.\n");
            }
            #endif
            
        }
        av_dict_free(&options);
            
    
            
        
        if(retval != SUCCEEDED){
            Close();
        }

    }
    catch(...){
        retval = UNEXPECTED;
    }
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
                    #ifndef __MINGW32__
                    pthread_join(context->CaptureThread, NULL);
                    #else
                    WaitForSingleObject(context->CaptureThread, INFINITE);
                    CloseHandle(context->CaptureThread);
                    #endif
                    avformat_close_input((AVFormatContext**)&context->DeviceHandle);
                    delete(context);
                    DeviceContext = NULL;
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
                deviceList.push_back(vid);
                printf("Device %d pushed to device list\n", x);
                avformat_close_input(&pFormatCtx);
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
#ifdef __linux__
        DIR *dp;
        struct dirent *dirp;
        if((dp  = opendir("/dev/")) == NULL) {
            retval = NO_DEVICES;
        }
        else{
            int index = 0;
            while ((dirp = readdir(dp)) != NULL) {
                string file(dirp->d_name);
                //std::cout << file << std::endl;
                if(file.find("audio", 0) != file.npos)
                {
                    file = "/dev/" + file;
                    int fd = open(file.c_str(), O_RDWR);
                    if(fd != -1)
                    {
                        v4l2_capability argp;
                        if(ioctl(fd, VIDIOC_QUERYCAP, &argp) == 0)
                        {
                            if(argp.capabilities & V4L2_CAP_STREAMING)
                            {
                                VideoInputDevice* vid = new VideoInputDevice();
                                vid->DeviceIndex = index;
                                string name((char*)argp.card);
                                vid->DeviceName = name;
                                
                                for(int x=0; x < StandardFormatCount; x++)
                                {
                                    v4l2_format rawfmt;
                                    memset(&rawfmt, 0, sizeof(v4l2_format));
                                    rawfmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                                    
                                    rawfmt.fmt.pix.width = StandardFormats[x].Width;
                                    rawfmt.fmt.pix.height = StandardFormats[x].Height;
                                    rawfmt.fmt.pix.pixelformat = (__u32)GetBPPFCC((VideoPixelFormat)StandardFormats[x].PixelFormat);
                                    if(ioctl(fd, VIDIOC_TRY_FMT, &rawfmt) == 0)
                                    {
                                        VideoMediaFormat* fmt = new VideoMediaFormat();
                                        fmt->Width = rawfmt.fmt.pix.width;
                                        fmt->Height = rawfmt.fmt.pix.height;
                                        fmt->PixelFormat = (VideoPixelFormat)StandardFormats[x].PixelFormat;
                                        vid->Formats.push_back(fmt);
                                        vid->FormatCount = vid->Formats.size();
                                    }
                                }
                                deviceList.push_back(vid);
                            }
                        }
                        
                        close(fd);
                    }
                    
                    index++;
                }
            }
            closedir(dp);
        }
#endif
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
