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
 * The Device_Errors enumeration defines the error codes that can be returned from
 * any function within the com.mti.primitives.devices namespace.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public enum Device_Errors {
    SUCCEEDED,
    NO_DEVICES,
    INVALID_DEVICE,
    INVALID_DATA,
    NO_INPUT,
    NO_OUTPUT,
    INVALID_FORMAT,
    NO_FORMATS,
    NOT_SUPPORTED,
    UNEXPECTED;
    
    public static Device_Errors FromNative(int val) throws Exception
    {
        Device_Errors[] vals = Device_Errors.values();
        if(val < 0 || val >= vals.length){
            throw new Exception("Invalid enumeration value.");
        }
        
        return vals[val];
    }
    
    public int ToNative()
    {
        return this.ordinal();
    }
}
