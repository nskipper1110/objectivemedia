package com.mti.primitives.devices;

/**
 * The VideoInputDevice class provides definition for accessing video input device
 * hardware.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/3/2013
 */
public final class VideoInputDevice extends InputDevice {
    
    /**
     * Constructs a new video input device based on the device index and name.
     * @param deviceIndex - The index of the device to use. This is related to the 
     * index of the device in the device list returned by the "GetDevices" function.
     * @param deviceName - The name of the device.
     */
    public VideoInputDevice(int deviceIndex, String deviceName){
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
    protected native int PlatformOpen(DeviceListener listener, int width, int height, int pixelFormat, int fps);
    
    /**
     * Provides platform-specific functionality for closing the device hardware
     * and resources.
     * @return A Device_Errors code.
     */
    protected native int PlatformClose();
    
    /**
     * Provides platform-specific functionality for retrieving a list of
     * devices.
     * @param deviceList - An array of VideoInputDevice elements, already instantiated
     * to have at least 10 elements. The function will populate the array with
     * available devices and leave all unused elements set to null.
     * @return Returns a Device_Errors code.
     */
    protected native int PlatformGetDevices(VideoInputDevice[] deviceList);
    
    /**
     * Opens the device with the given format.
     * @param format - The audio media format to use in opening the device.
     * @return Returns SUCCEEDED if the device was successfully opened, or an
     * error code if not.
     */
    public final Device_Errors Open(MediaFormat format){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            VideoMediaFormat vf = (VideoMediaFormat)format;
            if(vf == null){
                retval = Device_Errors.INVALID_FORMAT;
            }
            else{
                retval = Device_Errors.FromNative(PlatformOpen(this.Listener, vf.Width, vf.Height, vf.PixelFormat.ToNative(), vf.FPS));
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
     * Retrieves a list of available video input devices.
     * @param deviceList - The list to populate with the available input device.
     * @return Returns SUCCEEDED if the list was successfully populated, or an error
     * code if not.
     */
    public final Device_Errors GetDevices(java.util.List<Device> deviceList){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            VideoInputDevice[] objList = new VideoInputDevice[10];
            retval = Device_Errors.FromNative(PlatformGetDevices(objList));
            if(retval == Device_Errors.SUCCEEDED){
                if(deviceList == null){
                    deviceList = new java.util.ArrayList<Device>(); 
                }
                for(int x = 0; x < objList.length; x++){
                    if(objList[x] != null) deviceList.add((Device)objList[x]);
                }
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
}
