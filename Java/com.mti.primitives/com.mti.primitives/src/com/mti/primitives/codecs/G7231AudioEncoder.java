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
package com.mti.primitives.codecs;

import com.mti.primitives.devices.AudioMediaFormat;
import com.mti.primitives.devices.MediaFormat;

/**
 * This class provides functionality for implementing a G.723.1 audio encoder.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/4/2013
 */
public class G7231AudioEncoder extends Codec{
    public G7231AudioEncoder(){
        super();
    }
    /**
     * Provides platform-Specific functionality for opening the encoder.
     * @param encFormat - The audio media format for the encoder.
     * @param encData - The codec data used to encode the media.
     * @return Returns a Codec_Error code.
     */
    protected native int PlatformOpen(AudioMediaFormat encFormat, CodecData encData);
    /**
     * Provides the platform-specific functionality for closing the decoder.
     * @return Returns a Codec_Errors code.
     */
    protected native int PlatformClose();
    /**
     * Provides the platform-specific functionality for encoding a audio frame
     * into a g.723.1 packet.
     * @param inSample - The video frame to encode.
     * @param outSample - A reference to the array into which the encoded data will
     * be placed.
     * @param timestamp - The timestamp at which the frame was captured.
     * @return Returns a Codec_Errors code.
     */
    protected native int PlatformEncode(byte[] inSample, CodecResult outSample, long timestamp);
    /**
     * Provides the platform-specific functionality for decoding a audio frame
     * from a g.723.1 packet.
     * @param inSample - The g.723.1 packet to decode.
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
                retval = Codec_Errors.FromNative(PlatformOpen((AudioMediaFormat)encFormat, encData));
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
