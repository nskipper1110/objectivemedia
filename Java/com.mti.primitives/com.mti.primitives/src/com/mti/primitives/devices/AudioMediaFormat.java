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
 * The AudioMediaFormat provides the definition for an audio input or output device,
 * as well as the input or output of an audio codec.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public final class AudioMediaFormat extends MediaFormat {
    public final int BitsPerSample;
    public final int Channels;
    public final int SampleRate;
    
    /**
     * Instantiates a new AudioMediaFormat object with the given sample size,
     * channels, and sample rate.
     * @param bitsPerSample - The number of bits to use when sampling. Typically 8 or 16.
     * @param channels - The number of channels to sample.
     * @param sampleRate - The rate at which samples will be captured.
     */
    public AudioMediaFormat(int bitsPerSample, int channels, int sampleRate){
        BitsPerSample = bitsPerSample;
        Channels = channels;
        SampleRate = sampleRate;
    }
    
    public String toString(){
        return SampleRate + "x" + BitsPerSample + "x" + Channels;
    }
}
