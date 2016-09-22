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
import java.awt.*;
import java.awt.color.*;
import java.awt.image.*;
import java.awt.geom.*;
import java.util.*;
/**
 * The VideoOutputDevice class provides functionality for utilizing hardware
 * acceleration to display video frames to the screen.
 * @author Nathan Skipper, Montgomery Technology, Inc., nathan@montgomerytechnology.com
 * @version 1.0.0
 * @since 1/3/2013
 */
public final class VideoOutputDevice extends OutputDevice {
    /**
     * Maintains a reference to the format that was set when Open was called.
     */
    protected VideoMediaFormat CurrentFormat;
    /**
     * Gets or sets whether the device should transform each video frame by
     * rotating it by 180 degrees. If true, the rotation transform will be applied
     * to each frame.
     */
    public boolean RotateFrames;
    /**
     * Gets or sets the handle or pointer to the surface context. In Windows, this
     * is the Handle to the control onto which each frame should be drawn.
     */
    public Component Surface;
    /**
     * Instantiates a new VideoOutputDevice object based on the device index and name.
     * @param deviceIndex - The index of the video output device to implement. This
     * should correlate to the index of the device in the device list retrieved from
     * "GetDevices".
     * @param deviceName - The name of the device.
     */
    public VideoOutputDevice(int deviceIndex, String deviceName){
        super(deviceIndex, deviceName);
    }
    
    /**
     * Presents a frame to the device.
     * @param sample - A frame to present.
     * @param timestamp - The time stamp at which the frame was acquired.
     * @return Returns SUCCEEDED if the function successfully presented the frame,
     * or an error code if not.
     */
    public final Device_Errors Present(byte[] sample, long timestamp){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            if(Surface == null  || CurrentFormat == null){
                retval = Device_Errors.NO_OUTPUT;
            }
            else{
                Graphics surfaceGraphics = Surface.getGraphics();
                
                Rectangle size = Surface.getBounds();
                if(RotateFrames){
                    AffineTransform newXform = (AffineTransform)((Graphics2D)surfaceGraphics).getTransform().clone();
                    newXform.rotate(Math.toRadians(180), size.width/2, size.height/2);
                    ((Graphics2D)surfaceGraphics).setTransform(newXform);
                    
                }
                DataBuffer buffer = new DataBufferByte(sample, sample.length);
                int pixelStride = 3; //assuming r, g, b, skip, r, g, b, skip...
		int scanlineStride = 3 * ((VideoMediaFormat)CurrentFormat).Width; //no extra padding
                int[] bandOffsets = {2, 1, 0}; //r, g, b
                if(System.getProperty("os.name").toLowerCase().contains("mac")){
                    bandOffsets[0] = 0;
                    bandOffsets[2] = 2;
                }
		
		WritableRaster raster = Raster.createInterleavedRaster(buffer, ((VideoMediaFormat)CurrentFormat).Width, ((VideoMediaFormat)CurrentFormat).Height, scanlineStride, pixelStride, bandOffsets, null);
		ColorSpace colorSpace = ColorSpace.getInstance(ColorSpace.CS_sRGB);
                boolean hasAlpha = false;
                boolean isAlphaPremultiplied = false;
                int transparency = Transparency.OPAQUE;
                int transferType = DataBuffer.TYPE_BYTE;
                ColorModel colorModel = new ComponentColorModel(colorSpace, hasAlpha, isAlphaPremultiplied, transparency, transferType);
                BufferedImage img = new BufferedImage(colorModel, raster, false, null);
                surfaceGraphics.drawImage(img, 0,0, size.width, size.height, null);
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Gets a list of available video output devices.
     * @param deviceList - A reference to a list of device objects. This list
     * can be instantiated upon calling the function, or the function will instantiate
     * the list for you.
     * @return Returns SUCCEEDED if the device list was successfully populated,
     * or an error code if the device list could not be acquired.
     */
    public final Device_Errors GetDevices(java.util.List<Device> deviceList){
        Device_Errors retval = Device_Errors.NOT_SUPPORTED;
        try{
            
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Opens the device hardware and resources to prepare it for use. This function
     * assumes that the values for Surface, SurfaceWidth, SurfaceHeight, and RotateFrames
     * have already been set. If they have not, then this function will probably
     * return an error.
     * @param format - The format to use when opening the device.
     * @return Returns SUCCEEDED if the device was successfully opened, or an error
     * code if there was a problem opening the device.
     */
    public final Device_Errors Open(MediaFormat format){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            VideoMediaFormat vf = (VideoMediaFormat) format;
            if(vf == null){
                retval = Device_Errors.INVALID_FORMAT;
            }
            else if(Surface == null){
                retval = Device_Errors.NO_OUTPUT;
            }
            else if(vf.PixelFormat != VideoPixelFormat.RGB24 && vf.PixelFormat != VideoPixelFormat.ANY)
            {
                retval = Device_Errors.INVALID_FORMAT;
            }
            else{
                CurrentFormat = vf;
            }
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
    
    /**
     * Opens a device based on the format and output information provided. This
     * function sets the properties for the surface and then calls the standard
     * Open function.
     * @param format
     * @param surface
     * @param surfaceWidth
     * @param surfaceHeight
     * @param rotate
     * @return 
     */
    public final Device_Errors Open(VideoMediaFormat format, Component surface, boolean rotate){
        Surface = surface;
        RotateFrames = rotate;
        return Open(format);
    }
    
    /**
     * Closes the device hardware and resources.
     * @return Returns SUCCEEDED if the device was successfully closed, or
     * an error code if not.
     */
    public final Device_Errors Close(){
        Device_Errors retval = Device_Errors.SUCCEEDED;
        try{
            
        }
        catch(Exception e){
            retval = Device_Errors.UNEXPECTED;
        }
        return retval;
    }
}
