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
