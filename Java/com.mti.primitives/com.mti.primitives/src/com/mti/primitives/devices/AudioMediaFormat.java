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
