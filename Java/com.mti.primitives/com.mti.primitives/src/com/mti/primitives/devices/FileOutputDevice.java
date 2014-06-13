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
package com.mti.primitives.devices;

/**
 * The FileOutputDevice class provides definition for accessing file output device
 * hardware.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 6/6/2014
 */
public final class FileOutputDevice extends OutputDevice {

    @Override
    public Device_Errors Present(byte[] sample, long timestamp) {
        return Device_Errors.NOT_SUPPORTED;
    }
    
    public Device_Errors PresentAudio(byte[] sample, long timestamp){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            retval = Device_Errors.FromNative(PlatformPresentAudio(sample, sample.length, timestamp));
            
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    public Device_Errors PresentVideo(byte[] sample, long timestamp){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            retval = Device_Errors.FromNative(PlatformPresentVideo(sample, sample.length, timestamp));
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Constructs a new file output device based on the device index and name.
     * @param deviceIndex - The index of the device to use. This is related to the 
     * index of the device in the device list returned by the "GetDevices" function.
     * @param deviceName - The name of the device.
     */
    public FileOutputDevice(int deviceIndex, String deviceName){
        super(deviceIndex, deviceName);
    }
    
    /**
     * Provides the platform-specific functionality for opening the device hardware
     * and resources to use the device.
     * @param listener - The DeviceListener object that will be used for callbacks.
     * This parameter, even though it is loosely typed through Object, must be
     * directly related to the DeviceListener interface.
     * @param width - The width at which frames should be captured.
     * @param height - The height at which the frames should be captured.
     * @param pixelFormat - The pixel format at which frames should be captured.
     * @param fps - The Frames-Per-Second at which the frames should be captured.
     * @return Returns a Device_Errors success or error code.
     */
    protected native int PlatformOpen(String fileName, int width, int height, int sampleRate, int bitsPerSample, int channels);
    
    /**
     * Provides platform-specific functionality for closing the device hardware
     * and resources.
     * @return A Device_Errors code.
     */
    protected native int PlatformClose();
    
    protected native int PlatformPresentAudio(byte[] sample, long size, long timestamp);
    protected native int PlatformPresentVideo(byte[] sample, long size, long timestamp);
    
    
    /**
     * Opens the device with the given format.
     * @param format - The audio media format to use in opening the device.
     * @return Returns SUCCEEDED if the device was successfully opened, or an
     * error code if not.
     */
    public final Device_Errors Open(MediaFormat format){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            FileMediaFormat vf = (FileMediaFormat)format;
            if(vf == null){
                retval = Device_Errors.INVALID_FORMAT;
                System.out.println("FileMediaFormat is null");
            }
            else{
                retval = Device_Errors.FromNative(PlatformOpen(vf.FileName, vf.FrameWidth, vf.FrameHeight, vf.SampleRate, vf.BitsPerSample, vf.Channels));
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Closes the device and de-allocates resources.
     * @return Returns SUCCEEDED if the device was successfully closed, or an
     * error code if not.
     */
    public final Device_Errors Close(){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            retval = Device_Errors.FromNative(PlatformClose());
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Retrieves a list of available file output devices.
     * @param deviceList - The list to populate with the available output device.
     * @return Returns SUCCEEDED if the list was successfully populated, or an error
     * code if not.
     */
    public final Device_Errors GetDevices(java.util.List<Device> deviceList){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            retval = Device_Errors.NOT_SUPPORTED;
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
}
