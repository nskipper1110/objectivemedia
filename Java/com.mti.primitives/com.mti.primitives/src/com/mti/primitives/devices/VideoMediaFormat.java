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
