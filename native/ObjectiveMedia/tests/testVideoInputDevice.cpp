/* 
 * File:   testVideoInputDevice.cpp
 * Author: nathan
 *
 * Created on Jan 24, 2013, 8:07:22 PM
 */

#include <stdlib.h>
#include <iostream>
#include <vector>
#include "../platform/platform_devices.h"
/*
 * Simple C++ Test Suite
 */
using namespace std;

void testVideoInputDevice_GetDevices() {
    
    std::cout << "testVideoInputDevice_GetDevices (VideoInputDeviceTests)" << std::endl;
    VideoInputDevice* dev = new VideoInputDevice();
    vector<Device*> devices;
    Device_Errors err = dev->GetDevices(devices);
    if(err == SUCCEEDED)
    {
        std::cout << "testVideoInputDevice_GetDevices SUCCEEDED, devices to follow..." << std::endl;
        for(int x=0; x < devices.size(); x++)
        {
            VideoInputDevice* d = (VideoInputDevice*)devices[x];
            std::cout << "Device+++++++++++++++++++++++++++++++++++++++" << std::endl;
            std::cout << "DeviceName=" << d->DeviceName << std::endl;
            std::cout << "DeviceIndex=" << d->DeviceIndex << std::endl;
            std::cout << "Formats**************************************" << std::endl;
            for(int f = 0; f < d->Formats.size(); f++)
            {
                VideoMediaFormat* fmt = (VideoMediaFormat*)d->Formats[f];
                std::cout << "PixelFormat=" << fmt->PixelFormat << std::endl;
                std::cout << "Width=" << fmt->Width << std::endl;
                std::cout << "Height=" << fmt->Height << std::endl;
                std::cout << "*******************************************" << std::endl;
            }
        }
    }
    else{
        std::cout << "testVideoInputDevice_GetDevices FAILED with error " << err << std::endl;
    }
}

class MyDeviceListener : public DeviceListener{
    void SampleCaptured(void* sender, void* sample, long size, long long timestamp){
        
    }
};

void testVideoInputDevice_Open() {
    std::cout << "testVideoInputDevice_Open (VideoInputDeviceTests)" << std::endl;
    VideoInputDevice* dev = new VideoInputDevice();
    VideoMediaFormat* format = new VideoMediaFormat();
    format->PixelFormat = ANY;
    format->Width = 640;
    format->Height = 480;
    std::vector<Device*> devices;
    dev->GetDevices(devices);
    dev=(VideoInputDevice*)devices[0];
    dev->Listener = new MyDeviceListener();
    dev->Open(format);
    long wait = 15;
    
    timespec* tv = new timespec();
    tv->tv_nsec = 0;
    tv->tv_sec = wait;
    nanosleep(tv, NULL);
    
    dev->Close();
        
}

int main(int argc, char** argv) {
    std::cout << "%SUITE_STARTING% VideoInputDeviceTests" << std::endl;
    std::cout << "%SUITE_STARTED%" << std::endl;

    std::cout << "%TEST_STARTED% testVideoInputDevice_GetDevices (VideoInputDeviceTests)" << std::endl;
    testVideoInputDevice_GetDevices();
    std::cout << "%TEST_FINISHED% time=0 testVideoInputDevice_GetDevices (VideoInputDeviceTests)" << std::endl;

    std::cout << "%TEST_STARTED% testVideoInputDevice_Open (VideoInputDeviceTests)" << std::endl;
    testVideoInputDevice_Open();
    std::cout << "%TEST_FINISHED% time=0 testVideoInputDevice_Open (VideoInputDeviceTests)" << std::endl;

//    std::cout << "%TEST_STARTED% test2 (newsimpletest)\n" << std::endl;
//    test2();
//    std::cout << "%TEST_FINISHED% time=0 test2 (newsimpletest)" << std::endl;
//
//    std::cout << "%SUITE_FINISHED% time=0" << std::endl;

    return (EXIT_SUCCESS);
}

