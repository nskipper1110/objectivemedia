package com.mti.primitives.devices;

/**
 * This class is a superclass for any class that implements input device functionality.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public abstract class InputDevice extends Device {
    protected InputDevice(int deviceIndex, String deviceName){
        super(deviceIndex, deviceName);
    }
}
