package com.mti.primitives.codecs;

import com.mti.primitives.devices.*;

/**
 * This class provides definition for the h.263 video encoder.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/4/2013
 */
public class H263VideoEncoder extends Codec{
    public H263VideoEncoder(){
        super();
    }
    /**
     * Provides platform-Specific functionality for opening the encoder.
     * @param encFormat - The video media format for the encoder.
     * @param encData - The codec data used to encode the media.
     * @return Returns a Codec_Error code.
     */
    protected native int PlatformOpen(VideoMediaFormat encFormat, CodecData encData);
    /**
     * Provides the platform-specific functionality for closing the decoder.
     * @return Returns a Codec_Errors code.
     */
    protected native int PlatformClose();
    /**
     * Provides the platform-specific functionality for encoding a video frame
     * into a h.263 packet.
     * @param inSample - The video frame to encode.
     * @param outSample - A reference to the array into which the encoded data will
     * be placed.
     * @param timestamp - The timestamp at which the frame was captured.
     * @return Returns a Codec_Errors code.
     */
    protected native int PlatformEncode(byte[] inSample, CodecResult outSample, long timestamp);
    /**
     * Provides the platform-specific functionality for decoding a video frame
     * from a H.263 packet.
     * @param inSample - The h.263 packet to decode.
     * @param outSample - A reference to an array into which the decoded frame will
     * be placed.
     * @param timestamp - The time stamp at which the frame was captured/received.
     * @return Returns a Codec_error code.
     */
    protected native int PlatformDecode(byte[] inSample, CodecResult outSample, long timestamp);
    
    public final Codec_Errors Open(MediaFormat encFormat, CodecData encData){
        Codec_Errors retval = Codec_Errors.CODEC_SUCCEEDED;
        try{
            CurrentFormat = encFormat;
            CurrentData = encData;
            if(encData == null){
                retval = Codec_Errors.CODEC_INVALID_INPUT;
            }
            else if(encFormat == null){
                retval = Codec_Errors.CODEC_INVALID_INPUT;
            }
            else{
                retval = Codec_Errors.FromNative(PlatformOpen((VideoMediaFormat)encFormat, encData));
            }
            
        }
        catch(Exception e){
            retval = Codec_Errors.CODEC_UNEXPECTED;
        }
        return retval;
    }
    
    public final Codec_Errors Close(){
        Codec_Errors retval = Codec_Errors.CODEC_SUCCEEDED;
        try{
            retval = Codec_Errors.FromNative(PlatformClose());
        }
        catch(Exception e){
            retval = Codec_Errors.CODEC_UNEXPECTED;
        }
        return retval;
    }
    
    public final Codec_Errors Encode(byte[] inSample, CodecResult outSample, long timestamp){
        Codec_Errors retval = Codec_Errors.CODEC_SUCCEEDED;
        try{
            
            retval = Codec_Errors.FromNative(PlatformEncode(inSample, outSample, timestamp));
        }
        catch(Exception e){
            retval = Codec_Errors.CODEC_UNEXPECTED;
        }
        return retval;
    }
    
    public final Codec_Errors Decode(byte[] inSample, CodecResult outSample, long timestamp){
        Codec_Errors retval = Codec_Errors.CODEC_SUCCEEDED;
        try{
            retval = Codec_Errors.FromNative(PlatformDecode(inSample, outSample, timestamp));
        }
        catch(Exception e){
            retval = Codec_Errors.CODEC_UNEXPECTED;
        }
        return retval;
    }
}
