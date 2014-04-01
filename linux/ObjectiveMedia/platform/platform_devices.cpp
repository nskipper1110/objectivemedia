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
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <assert.h>

#include <getopt.h>             /* getopt_long() */

#include <fcntl.h>              /* low-level i/o */
#include <unistd.h>
#include <errno.h>
#include <malloc.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>

#include <asm/types.h>          /* for videodev2.h */

#include <linux/videodev2.h>
/********************************************
Linux Specific Structures and functions
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
    int DeviceHandle;
    long ImageSize;
    VideoMediaFormat* Format;
    pthread_t CaptureThread;
    DeviceListener* Listener;
    bool Stopped;
    VideoInputBuffer* Buffers;
    unsigned int BufferCount;
    AVFrame* TempFrame;
    SwsContext* ScaleContext;
    VideoInputDeviceContext(){
        DeviceHandle = -1;
        ImageSize = 0;
        Format = NULL;
        CaptureThread = -1;
        Listener = NULL;
        Stopped = false;
        Buffers = NULL;
        BufferCount = 0;
        TempFrame = NULL;
        ScaleContext = NULL;
    };
    ~VideoInputDeviceContext(){
        if(Buffers != NULL)
            free(Buffers);
        BufferCount = 0;
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
    pthread_t CaptureThread;
    DeviceListener* Listener;
    bool Stopped;
    
    AudioInputDeviceContext(){
        DeviceHandle = -1;
        Format = NULL;
        CaptureThread = -1;
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
        case UNKNOWN:
            retval = V4L2_PIX_FMT_H264;
            break;
        default:
            retval = V4L2_PIX_FMT_BGR24;
    }
    return retval;
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
	this->DeviceName = "";
	this->DeviceIndex = 0;
	this->Listener = NULL;
	this->DeviceContext = NULL;
	FormatCount = 0;
}

 void *VideoInputDevice_Thread(void* ptr){
    VideoInputDeviceContext* context = (VideoInputDeviceContext*) ptr;
    if(context->Format->FPS <= 0) context->Format->FPS = 20;
    double adjfps = context->Format->FPS;
    long sleepTime = 1000000*((double) 1000/adjfps);
    while(!context->Stopped){
        v4l2_buffer buf;
        memset (&buf, 0, sizeof(buf));

        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;

        if (0 == ioctl (context->DeviceHandle, VIDIOC_DQBUF, &buf)) {
            if(context->Listener != NULL)
            {
                void* buffer = context->Buffers[buf.index].Buffer;
                int bufsize = buf.length;
                if(context->ScaleContext != NULL){
                    VideoMediaFormat* vf = context->Format;
                    AVFrame* source = alloc_and_fill_picture((AVPixelFormat)VideoMediaFormat::GetFFPixel(vf->PixelFormat), vf->Width, vf->Height, buffer);
                    if(source != NULL){
                        int outheight = sws_scale(context->ScaleContext, source->data, source->linesize,0, vf->Height, context->TempFrame->data, context->TempFrame->linesize);
                        //set the outgoing reference.
                        if(outheight > 0)
                        {
                            buffer = context->TempFrame->data[0];
                                //calculate and set the outgoing frame size, in bytes.
                            bufsize = vf->Width * vf->Height * VideoMediaFormat::GetPixelBits(RGB24) / 8;
                        }
                        av_free(source);
                    }
                }
                context->Listener->SampleCaptured(NULL, buffer, bufsize, 0);
            }
            ioctl (context->DeviceHandle, VIDIOC_QBUF, &buf);
        }

        

        timespec tv;
        tv.tv_nsec = sleepTime;
        tv.tv_sec = 0;
        
        nanosleep(&tv, NULL);
    }
    pthread_exit(NULL);
}

Device_Errors VideoInputDevice::Open(MediaFormat* format){
    Device_Errors retval = SUCCEEDED;
    try
    {
        string file("/dev/video");
        char index[3];
        sprintf(index,"%d", DeviceIndex, 10);
        file = file + index;
        VideoMediaFormat* vformat = (VideoMediaFormat*)format;
        VideoInputDeviceContext* context = new VideoInputDeviceContext();
        
        if(vformat->AVPixelFormat == ANY){
            for(int x = 0; x < Formats.size(); x++){
                VideoMediaFormat* f = (VideoMediaFormat*)Formats[x];
                if(vformat->Width == f->Width && vformat->Height == f->Height){
                    vformat->PixelFormat = f->PixelFormat;
                    PixelFormat fmt = (PixelFormat)VideoMediaFormat::GetFFPixel(RGB24);
                    context->TempFrame = alloc_picture(fmt, vformat->Width, vformat->Height); //allocate temp based on this format.
                    context->ScaleContext = sws_getContext(vformat->Width, vformat->Height,(AVPixelFormat)VideoMediaFormat::GetFFPixel(vformat->PixelFormat), vformat->Width, vformat->Height,fmt,SWS_BICUBIC, NULL, NULL, NULL);
                    break;
                }
            }
        }
        context->DeviceHandle = -1;
        context->Format = vformat;
        context->DeviceHandle = open(file.c_str(), O_RDWR | O_NONBLOCK);
        if(context->DeviceHandle == -1)
        {
            retval = INVALID_DEVICE;
        }
        else{
            v4l2_input input;
            memset(&input, 0, sizeof(input));
            int counter = 0;
            input.index = counter;
            
            if(ioctl(context->DeviceHandle, VIDIOC_ENUMINPUT, &input) != -1){
                if((input.status & V4L2_IN_ST_HFLIP) != 0){
                    input.status = input.status ^ V4L2_IN_ST_HFLIP;
                }
                if((input.status & V4L2_IN_ST_VFLIP) != 0){
                    input.status = input.status ^ V4L2_IN_ST_VFLIP;
                }
                if(ioctl(context->DeviceHandle, VIDIOC_S_INPUT, &input) != -1){
                    v4l2_std_id std_id = V4L2_STD_NTSC;
                    ioctl (context->DeviceHandle, VIDIOC_S_STD, &std_id);
                    v4l2_cropcap cropcap;
                    v4l2_crop crop;

                    memset (&cropcap, 0, sizeof(cropcap));

                    cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

                    if (0 == ioctl (context->DeviceHandle, VIDIOC_CROPCAP, &cropcap)) {
                            crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                            crop.c = cropcap.defrect; /* reset to default */

                            if (-1 == ioctl (context->DeviceHandle, VIDIOC_S_CROP, &crop)) {
                                    switch (errno) {
                                    case EINVAL:
                                            /* Cropping not supported. */
                                            break;
                                    default:
                                            /* Errors ignored. */
                                            break;
                                    }
                            }
                    } else {        
                            /* Errors ignored. */
                    }

                    v4l2_format rawfmt;
                    memset(&rawfmt, 0, sizeof(v4l2_format));
                    rawfmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

                    rawfmt.fmt.pix.width = vformat->Width;
                    rawfmt.fmt.pix.height = vformat->Height;
                    rawfmt.fmt.pix.field = V4L2_FIELD_ANY;

                    rawfmt.fmt.pix.pixelformat = (__u32)GetBPPFCC((VideoPixelFormat)vformat->PixelFormat);
                    if(ioctl(context->DeviceHandle, VIDIOC_S_FMT, &rawfmt) == -1)
                    {
                        retval = INVALID_FORMAT;
                    }
                    else{
                        context->Listener = Listener;
                        DeviceContext = context;
                        context->Stopped = false;
                        context->ImageSize = rawfmt.fmt.pix.sizeimage;

                        v4l2_requestbuffers req;

                        memset (&req,0, sizeof(req));

                        req.count               = 4;
                        req.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                        req.memory              = V4L2_MEMORY_MMAP;

                        if (0 == ioctl (context->DeviceHandle, VIDIOC_REQBUFS, &req)) {
                                if (req.count >= 2) {
                                   context->Buffers = (VideoInputBuffer*)calloc (req.count, sizeof (*context->Buffers));

                                    for (context->BufferCount = 0; context->BufferCount < req.count; ++context->BufferCount) {
                                            v4l2_buffer buf;

                                            memset (&buf, 0, sizeof(buf));

                                            buf.type        = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                                            buf.memory      = V4L2_MEMORY_MMAP;
                                            buf.index       = context->BufferCount;

                                            if (0 == ioctl (context->DeviceHandle, VIDIOC_QUERYBUF, &buf))
                                            {
                                                context->Buffers[context->BufferCount].Length = buf.length;
                                                context->Buffers[context->BufferCount].Buffer =
                                                        mmap (NULL /* start anywhere */,
                                                              buf.length,
                                                              PROT_READ | PROT_WRITE /* required */,
                                                              MAP_SHARED /* recommended */,
                                                              context->DeviceHandle, buf.m.offset);
                                                if(MAP_FAILED == context->Buffers[context->BufferCount].Buffer)
                                                    break;
                                            }


                                    } 
                                   for (int i = 0; i < context->BufferCount; ++i) {
                                        struct v4l2_buffer buf;

                                        memset (&buf, 0, sizeof(buf));

                                        buf.type        = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                                        buf.memory      = V4L2_MEMORY_MMAP;
                                        buf.index       = i;

                                        if(-1 == ioctl (context->DeviceHandle, VIDIOC_QBUF, &buf))
                                            printf("QBuf Failed");
                                }

                                //v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

                                if(-1 == ioctl (context->DeviceHandle, VIDIOC_STREAMON, &rawfmt.type))
                                {
                                    retval = NOT_SUPPORTED;
                                }
                                else{
                                    int r = pthread_create( &context->CaptureThread, NULL, &VideoInputDevice_Thread, (void*) DeviceContext);
                                    if(r != 0){
                                        retval = NOT_SUPPORTED;
                                    }
                                }
                            }


                        }


                    }
                }
                else{
                    retval = INVALID_DEVICE;
                }
            }
            else{
                retval = INVALID_DEVICE;
            }
            
            
            
        }
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
                        pthread_join(context->CaptureThread, NULL);
                        enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                        ioctl(context->DeviceHandle, VIDIOC_STREAMOFF, &type);
                        for (int i = 0; i < context->BufferCount; ++i)
                                munmap(context->Buffers[i].Buffer, context->Buffers[i].Length);
                        close(context->DeviceHandle);
                        free(context->Buffers);
                        context->Buffers = NULL;
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
                if(file.find("video", 0) != file.npos)
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
                                const char* text = file.c_str();
                                int len = strlen(text);
                                int i = (int) text[len - 1];
                                i = i - 48;
                                vid->DeviceIndex = i;
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
    }
    catch(...)
    {
        retval = UNEXPECTED;
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
