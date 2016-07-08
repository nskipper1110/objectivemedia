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
 * The Device class serves as the superclass for all device classes within this
 * namespace. Any class that provides functionality for accessing media device
 * functionality should inherit this class.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public abstract class Device {
    /**
     * The index of the device in the list of available devices of this type.
     */
    public final int DeviceIndex;
    /**
     * The name of the device.
     */
    public final String DeviceName;
    /**
     * A list of available media formats for this device.
     */
    public java.util.List<MediaFormat> Formats;
    /**
     * The device listener for this device. This listener will receive callbacks
     * for the device.
     */
    public DeviceListener Listener;
    
    public long Primitive = 0;
    
    /**
     * Instantiates a new Device object with the given parameters.
     * @param deviceIndex - The index of the device in the list of available devices.
     * @param deviceName - The name of the device.
     */
    protected Device(int deviceIndex, String deviceName){
        DeviceIndex = deviceIndex;
        DeviceName = deviceName;
        Formats = new java.util.ArrayList<MediaFormat>();
        Listener = null;
    }
    
    /**
     * Causes the device to allocate all necessary resources and begin performing
     * its media operation.
     * @param format - The format to use when capturing or presenting media.
     * @return Returns "SUCCEEDED" if the operation successfully opened. Otherwise
     * it returns an error code.
     */
    public abstract Device_Errors Open(MediaFormat format);
    
    /**
     * Closes the device and causes the device to stop its media operation and
     * deallocate all resources.
     * @return Returns SUCCEEDED if the operation successfully closed. Otherwise
     * it returns an error code.
     */
    public abstract Device_Errors Close();
    
    /**
     * Retrieves a list of available devices of the object's media type.
     * @param deviceList - A list to populate with the available devices of this type.
     * @return Returns SUCCEEDED if the operation successfully loaded devices, otherwise
     * it returns an error code.
     */
    public abstract Device_Errors GetDevices(java.util.List<Device> deviceList);
    
    /**
     * Allocates a native buffer in memory for use later. This allocation occurs
     * in unmanaged memory and should be followed by a call to FreeBuffer when
     * the memory is no longer needed.
     * @param size - The size, in bytes, of the buffer to allocate.
     * @return - Returns 0 if no memory was allocated, or a memory address represented
     * as a long integer if successful.
     */
    public static native long AllocBuffer(int size);
    
    /**
     * Frees the memory allocated by AllocBuffer.
     * @param buffer - A long integer representation of the address in memory for the buffer.
     */
    public static native void FreeBuffer(long buffer);
    
    public String toString(){
        return DeviceName;
    }
}
