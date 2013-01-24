package com.mti.primitives.devices;

/**
 * The VideoPixelFormat enumeration provides a list of supported pixel formats.
 * @author Nathan Skipper, Montgomery Technology, Inc. nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public enum VideoPixelFormat {
    RGB1(1), //1 bit
    RGB4(4), //4 bit
    RGB8(8), //8 bit
    RGB555(15), //15 bit
    RGB565(16), //16 bit
    RGB24(24), //24 bit
    RGB32(31), //32 bit
    ARGB32(32), //32 bit
    AYUV(65), //32 bit
    UYVY(66), //16 bit
    Y411(67), //12 bit
    Y41P(68), //12 bit
    Y211(69), //8 bit
    YUY2(70), //16 bit
    YVYU(71), //16 bit
    YUYV(72), //16 bit
    IF09(73), //9.5 bits
    IYUV(74), //12 bits
    YV12(75), //12 bits
    YVU9(76), //9 buts
    I420(77), //12 bits
    UNKNOWN(99), //unknown pixel size.
    ANY(0); //any pixel size.

    protected int Value = 0;

    VideoPixelFormat(int val){
        Value = val;
    }

    public static VideoPixelFormat FromNative(int val) throws Exception
    {
        VideoPixelFormat retval = null;
        for(int x = 0; x < VideoPixelFormat.values().length; x++){
            if(VideoPixelFormat.values()[x].ToNative() == val){
                retval = VideoPixelFormat.values()[x];
                break;
            }
        }
        if(retval == null){
            throw new Exception("Invalid enumeration value.");
        }
        return retval;
    }

    public int ToNative()
    {
        return Value;
    }
}
