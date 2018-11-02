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

import javax.sound.sampled.*;

/**
 * This class provides functionality for outputting to an audio device.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/3/2013
 */
public final class AudioOutputDevice extends OutputDevice{
    /**
     * Sets the current audio media format used by the device.
     */
    protected AudioMediaFormat CurrentFormat;
    private Mixer MyMixer;
    private SourceDataLine MyLine;
    /**
     * Constructs a new object with the given index and device name.
     * @param deviceIndex - The index of the device from the list of devices
     * acquired by the "GetDevices" function.
     * @param deviceName - The name of the device.
     */
    public AudioOutputDevice(int deviceIndex, String deviceName){
        super(deviceIndex, deviceName);
        
    }
    
    /**
     * Opens the audio output device and prepares it for use.
     * @param format - The AudioMediaFormat to use when opening the device.
     * @return Returns SUCCEEDED if the audio output device was successfully opened
     * or a failure code if not.
     */
    public final Device_Errors Open(MediaFormat format){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            AudioMediaFormat af = (AudioMediaFormat)format;
            if(af == null){
                retval = Device_Errors.INVALID_FORMAT;
            }
            else{
                try{
                    CurrentFormat = af;
                    
                    AudioFormat jformat = new AudioFormat(AudioFormat.Encoding.PCM_SIGNED,(float)af.SampleRate, af.BitsPerSample, af.Channels, (af.BitsPerSample/8*af.Channels), af.SampleRate,false);
                    
                    MyLine = AudioSystem.getSourceDataLine(jformat);
                    MyLine.open(jformat);
                    MyLine.start();
                }
                catch(Exception e){
                    retval = Device_Errors.INVALID_FORMAT;
                }
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Closes the audio output device and de-allocates resources.
     * @return Returns SUCCEEDED if the device was successfully close, or an
     * error code if not.
     */
    public final Device_Errors Close(){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            MyLine.stop();
            MyLine.close();
            
            MyLine = null;
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Retrieves a list of all available audio output devices.
     * @param deviceList - A list, into which available audio devices will be put.
     * The list can be instantiated at the time of call, or the function will instantiate
     * the parameter.
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
    
    /**
     * Presents an array of samples to the audio device for playing.
     * @param samples - An array of samples to play.
     * @param timestamp - The time stamp at which the samples were acquired.
     * @return Returns SUCCEEDED if the samples were successfully presented, or
     * an error code if not.
     */
    public final Device_Errors Present(byte[] samples, long timestamp){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            
            if(MyLine == null)
            {
                retval = Device_Errors.NO_OUTPUT;
            }
            else if(!MyLine.isOpen()){
                retval = Device_Errors.NO_OUTPUT;
            }
            else{
                MyLine.write(samples, 0, samples.length);
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
}
