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
 * This class provides functionality for accessing audio input device hardware.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/3/2013
 */
public final class AudioInputDevice extends InputDevice{
    
    private Mixer MyMixer;
    private TargetDataLine MyLine;
    private Thread MyThread;
    private boolean stopped = false;
    public AudioMediaFormat CurrentFormat;
    private class MyThreadRunner implements Runnable{
        private AudioInputDevice Boss = null;
        private long StartTime = 0;
        public MyThreadRunner(AudioInputDevice boss){
            Boss = boss;
            StartTime = System.currentTimeMillis();
        }
        public void run()
        {
            while(!stopped){
                try{
                    if(MyMixer == null || MyLine == null || Listener == null){
                        stopped = true;
                        break;
                    }
                    else{
                        if(MyLine.available() > 0){
                            int bufSize = 240 * CurrentFormat.BitsPerSample / 8 * CurrentFormat.Channels;
                            byte[] buffer = new byte[bufSize];
                            int ret = MyLine.read(buffer, 0, bufSize);
                            if(ret > 0)
                            {
                                Listener.SampleCaptured(Boss, buffer, System.currentTimeMillis() - StartTime);
                            }
                        }
                    }
                    double delay = ((double)CurrentFormat.SampleRate / 240) * 0.50;
                    Thread.sleep((int)delay);
                }catch(Exception e){
                    String a = e.getMessage();
                    a = a;
                }
                
            }
        }
    }
    
    /**
     * Constructs a new object with the given index and name.
     * @param deviceIndex - The index of the audio device to use, related to the
     * index of the device in the "GetDevices" list.
     * @param deviceName -The name of the device.
     */
    public AudioInputDevice(int deviceIndex, String deviceName){
        super(deviceIndex, deviceName);
        try{
            Mixer.Info[] Mixers = AudioSystem.getMixerInfo();
            if(DeviceIndex < Mixers.length)
            {
                MyMixer = AudioSystem.getMixer(Mixers[DeviceIndex]);
                Line.Info[] targets = MyMixer.getTargetLineInfo();
                if(Formats == null){
                    Formats = new java.util.ArrayList<MediaFormat>();
                }
                for(int i = 0; i < targets.length; i++){
                    try{
                        AudioFormat[] formats = ((DataLine.Info)targets[i]).getFormats();
                        for(AudioFormat format : formats){
                            if(format.getEncoding() == AudioFormat.Encoding.PCM_SIGNED){
                                Formats.add((MediaFormat)new AudioMediaFormat(format.getSampleSizeInBits(), format.getChannels(), (int)format.getSampleRate()));
                            }
                        }
                    }
                    catch(Exception e){}
                }
            }
        }
        catch(Exception e){}
    }
    
    
    private native int PlatformOpen(AudioMediaFormat format);
    
    private native int PlatformGetDevices(java.util.List<Device> deviceList);
    
    private native int PlatformClose();
    /**
     * Opens the audio input device and allocates resources for use.
     * @param format - The format to use when opening the device.
     * @return Returns SUCCEEDED if the device is opened successfully, or error
     * if not.
     */
    public final Device_Errors Open(MediaFormat format){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            AudioMediaFormat af = (AudioMediaFormat)format;
            if(af == null){
                retval = Device_Errors.INVALID_FORMAT;
            }
            else if(MyMixer == null){
                retval = Device_Errors.INVALID_DEVICE;
            }
            else{
                try{
                    CurrentFormat = af;
                    
                    AudioFormat jformat = new AudioFormat(AudioFormat.Encoding.PCM_SIGNED,(float)af.SampleRate, af.BitsPerSample, af.Channels, (af.BitsPerSample/8*af.Channels), af.SampleRate,false);
                    
                    MyLine = AudioSystem.getTargetDataLine(jformat, MyMixer.getMixerInfo());
                    MyLine.open(jformat);
                    MyLine.start();
                    stopped = false;
                    MyThread = new Thread(new MyThreadRunner(this));
                    MyThread.start();
                }
                catch(Exception e){
                    retval = Device_Errors.NO_INPUT;
                }
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Closes the audio input device and de-allocates resources.
     * @return Returns SUCCEEDED if the device was successfully closed, or error
     * if not.
     */
    public final Device_Errors Close(){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            stopped = true;
            Thread.sleep(0);
            MyLine.stop();
            
            MyThread = null;
            MyLine.close();
            MyMixer.close();
            MyLine = null;
            
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Retrieves a list of available audio input devices.
     * @param deviceList - A list to populate with the available devices. If the
     * list isn't instantiated, the function will do so.
     * @return Returns SUCCEEDED if the function successfully loaded audio devices,
     * or an error code if not.
     */
    public final Device_Errors GetDevices(java.util.List<Device> deviceList){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            
            if(deviceList == null){
                deviceList = new java.util.ArrayList<Device>(); 
            }
            Mixer.Info[] Mixers = AudioSystem.getMixerInfo();
            if(Mixers.length == 0){
                retval = Device_Errors.NO_DEVICES;
            }
            else{
                
                for(int x = 0; x < Mixers.length; x++){
                    Mixer m = AudioSystem.getMixer(Mixers[x]);
                    
                    Mixer.Info info = m.getMixerInfo();
                    System.out.println("Mixer " + info.getName() + " by " + info.getVendor() + ": " + info.getDescription());
                    Line.Info[] targets = m.getTargetLineInfo();
                    for(int i = 0; i < targets.length; i++){
                        try{
                            System.out.println("\tTarget: " + targets[i].toString());
                            AudioFormat[] formats = ((DataLine.Info)targets[i]).getFormats();
                            for(AudioFormat format : formats){
                                System.out.println("\t\tFormat: " + format.getEncoding() + "x" + format.getSampleRate() + "x" + format.getSampleSizeInBits() + "x" + format.getChannels());
                            }
                        }
                        catch(Exception e){}
                    }
                    if(!info.getName().toLowerCase().contains("java") && targets.length > 0){
                        AudioInputDevice aid = new AudioInputDevice(x, info.getName());
                        deviceList.add(aid);
                    }
                }
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
}
