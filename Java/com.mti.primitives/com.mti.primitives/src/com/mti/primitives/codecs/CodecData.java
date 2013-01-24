package com.mti.primitives.codecs;

/**
 * The CodecData class provides definitions for any codec implemented under this namespace.
 * This class can be extended to provide additional fields.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/4/2013
 */
public class CodecData {
    /**
     * The bit rate at which the codec should compress the data.
     */
    public final int BitRate;
    /**
     * The crispness the codec should use.
     */
    public final int Crispness;
    /**
     * Sets whether the codec should use variable bit rate encoding or not. If true,
     * VBR should be used, otherwise false.
     */
    public final boolean IsVariableBitRate;
    /**
     * Sets the number of frames between key frames/i-frames.
     */
    public final int KeyFrameSpace;
    /**
     * Gets or sets the compression quality, used by VBR encoders.
     */
    public final int Quality;
    
    /**
     * Constructs a new object given the codec parameters.
     * @param bitRate - The bit rate for the codec.
     * @param crispness - The crispness for the codec.
     * @param isVariableBitRate - Whether to use VBR encoding.
     * @param keyFrameSpace - The key frame space for the coding.
     * @param quality - The quality of the encoding.
     */
    public CodecData(int bitRate, int crispness, boolean isVariableBitRate, int keyFrameSpace, int quality){
        BitRate = bitRate;
        Crispness = crispness;
        IsVariableBitRate = isVariableBitRate;
        KeyFrameSpace = keyFrameSpace;
        Quality = quality;
    }
}
