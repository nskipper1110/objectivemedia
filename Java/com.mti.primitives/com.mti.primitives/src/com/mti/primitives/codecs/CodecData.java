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
