package com.mti.primitives.codecs;

import com.mti.primitives.devices.MediaFormat;

/**
 * The Codec class serves as the superclass for all Encoders or Decoders implemented
 * within this namespace.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.1
 * @since 1/22/2013
 * Revision History:
 * 1.0.0 - Initial Creation
 * 1.0.1 - 1/22/2013 - Changed Encode and decode functions to use CodecResult for return.
 */
public abstract class Codec {
    /**
     * The current codec definition used for the codec.
     */
    public CodecData CurrentData;
    /**
     * The current media format used by the codec.
     */
    public MediaFormat CurrentFormat;
    /**
     * Initiates the basic fields.
     */
    protected Codec(){
        CurrentData = null;
        CurrentFormat = null;
    }
    
    /**
     * Opens the codec and allocates the resources to prepare it for use.
     * @param encFormat - The media format that is presented to the encoder. In the case
     * of decoding, the value specifies the desired output of the decoding.
     * @param encData - The parameters used to encode/decode the media.
     * @return Returns SUCCEEDED if the codec successfully opened, or an error code
     * if it fails.
     */
    public abstract Codec_Errors Open(MediaFormat encFormat, CodecData encData);
    /**
     * Closes the resources and the codec.
     * @return Returns SUCCEEDED if the codec was successfully closed, or an error
     * code if not.
     */
    public abstract Codec_Errors Close();
    /**
     * Encodes a sample of media and provides the encoded media back through the parameters.
     * @param inSample - The sample to encode.
     * @param outSample - A reference to an array that will be populated with the
     * encoded data.
     * @param timestamp - The time stamp for the sample. Mostly, this parameter is not used.
     * @return Returns SUCCEEDED if the data is successfully encoded, or an error code
     * if not.
     */
    public abstract Codec_Errors Encode(byte[] inSample, CodecResult outSample, long timestamp);
    /**
     * Decodes a sample of media.
     * @param inSample - The encoded media that needs to be decoded.
     * @param outSample - A reference to an array that will be populated with the
     * decoded media.
     * @param timestamp - The timestamp for the sample. Mostly not used.
     * @return Returns SUCCEEDED if the packet was successfully decoded, or an error
     * code if not.
     */
    public abstract Codec_Errors Decode(byte[] inSample, CodecResult outSample, long timestamp);
}
