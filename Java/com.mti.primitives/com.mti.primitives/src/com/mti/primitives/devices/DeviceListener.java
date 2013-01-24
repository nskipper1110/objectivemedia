package com.mti.primitives.devices;

/**
 * The DeviceListener interface provides a means of callback so from a device
 * to a caller.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public interface DeviceListener {
    void SampleCaptured(Device sender, byte[] sample, long timestamp);
}
