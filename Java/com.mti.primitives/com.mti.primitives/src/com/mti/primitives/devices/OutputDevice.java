package com.mti.primitives.devices;

/**
 * The OutputDevice class is an abstract superclass for any device that provides
 * output functionality. Any class that implements functionality for an output
 * device should extend this class.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public abstract class OutputDevice extends Device {
    protected OutputDevice(int deviceIndex, String deviceName){
        super(deviceIndex, deviceName);
    }
    /**
     * Presents the provided media through the output device.
     * @param sample - An array representing the sample(s) to present.
     * @param timestamp - The time stamp at which the sample was acquired.
     * @return - Returns SUCCEEDED if the operation successfully presented the sample,
     * or an error code if it failed.
     */
    public abstract Device_Errors Present(byte[] sample, long timestamp);
}
