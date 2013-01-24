
package com.mti.primitives.codecs;

/**
 * The Codec_Errors enumeration defines the possible error codes that can
 * be returned from within the com.mti.primitives.codecs namespace.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public enum Codec_Errors {
    CODEC_SUCCEEDED,
    CODEC_NOT_SUPPORTED,
    CODEC_CODEC_NOT_OPENED,
    CODEC_FAILED_TO_OPEN,
    CODEC_UNAVAILABLE,
    CODEC_INVALID_INPUT,
    CODEC_NO_OUTPUT,
    CODEC_UNEXPECTED;
    
    public static Codec_Errors FromNative(int val) throws Exception
    {
        Codec_Errors[] vals = Codec_Errors.values();
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
