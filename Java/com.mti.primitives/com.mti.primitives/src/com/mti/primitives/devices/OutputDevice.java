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
