package com.mti.primitives.devices;

/**
 * The VideoMediaFormat class extends the MediaFormat class to provide definition
 * for video formats.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 12/21/2012
 */
public final class VideoMediaFormat extends MediaFormat{
    public final int FPS;
    public final int Width;
    public final int Height;
    public final VideoPixelFormat PixelFormat;
    
    /**
     * Constructs a new VideoMediaFormat object with the given format values.
     * @param fps - The Frames-Per-Second for the format.
     * @param width - The width, in pixels, of the video frame.
     * @param height - The height, in pixels, of the video frame.
     * @param pixelFormat - The pixel format of the video frame.
     */
    public VideoMediaFormat(int fps, int width, int height, VideoPixelFormat pixelFormat){
        FPS = fps;
        Width = width;
        Height = height;
        PixelFormat = pixelFormat;
    }
    
    public String toString(){
        return Width + "x" + Height + "@" + PixelFormat.toString();
    }
}
