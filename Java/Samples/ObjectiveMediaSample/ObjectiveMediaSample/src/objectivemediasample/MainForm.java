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
package objectivemediasample;
import com.mti.primitives.codecs.*;
import com.mti.primitives.devices.*;

import java.util.*;
import javax.swing.*;
import java.awt.event.*;
import java.awt.*;
import java.awt.color.*;
import java.awt.image.*;
import java.awt.geom.*;
import java.io.*;

/**
 *
 * @author nathan
 */
public class MainForm extends javax.swing.JFrame {

    private java.util.concurrent.ConcurrentLinkedQueue<byte[]> AudioQueue = new java.util.concurrent.ConcurrentLinkedQueue<byte[]>();
    private javax.swing.Timer AudioTimer = null;
    private FileOutputDevice FileOutput = null;
    private class MyVideoDeviceListener implements DeviceListener{
        private long FrameCount = 0;
        private long StartTime = 0;
        private long CurrentTime = 0;
        private long TotalBits = 0;
        public void SampleCaptured(Device sender, byte[] sample, long timestamp){
            if(CurrentVideoOutputDevice != null)
            {
                byte[] encSample = new byte[1];
                byte[] decSample = null;
                if(FileOutput != null){
                    FileOutput.PresentVideo(sample, timestamp);
                }
                CodecResult decResult = new CodecResult();
                if(CurrentVideoEncoder != null){
                    if(CurrentVideoEncoder.Encode(sample, decResult, timestamp) == Codec_Errors.CODEC_SUCCEEDED){
                        if(decResult.Result != null)
                        {
                            if(StartTime == 0) {
                                StartTime = System.currentTimeMillis();
                                CurrentTime = StartTime;
                            }
                            FrameCount++;
                            TotalBits += decResult.Result.length;
                            if(System.currentTimeMillis() - CurrentTime >= 1000){
                                double time = CurrentTime - StartTime;
                                time = time/1000;
                                CurrentTime = System.currentTimeMillis();
                                long FrameRate = FrameCount;
                                
                                double BitRate = (TotalBits*8);
                                BitRate = BitRate/time;
                                lblH263FrameRate.setText(FrameRate + "");
                                lblH263BitRate.setText(((int)BitRate) + "");
                                FrameCount = 0;
                                
                            }
                        }
                        if(CurrentVideoDecoder != null && decResult.Result != null)
                        {
                            if(CurrentVideoDecoder.Decode(decResult.Result, decResult, timestamp) != Codec_Errors.CODEC_SUCCEEDED){
                                decSample = sample;
                            }
                            else{
                                decSample = decResult.Result;
                            }
                        }
                        else{
                            decSample = sample;
                        }
                    }
                    else{
                        decSample = sample;
                    }
                }
                else{
                    decSample = sample;
                }
                CurrentVideoOutputDevice.Present(decSample, timestamp);
            }
        }
    }
    
    private class MyAudioDeviceListener implements DeviceListener{
        long CurrentTime = 0;
        long TotalBits = 0;
        public void SampleCaptured(Device sender, byte[] sample, long timestamp){
            if(FileOutput != null){
                FileOutput.PresentAudio(sample, timestamp);
            }
            
            if(CurrentAudioEncoder != null && CurrentAudioDecoder != null){
                CodecResult result = new CodecResult();
                if(CurrentAudioEncoder.Encode(sample, result, timestamp) == Codec_Errors.CODEC_SUCCEEDED){
                    if(CurrentTime == 0){
                        CurrentTime = System.currentTimeMillis();
                    }
                    TotalBits += result.Result.length * 8;
                    if(System.currentTimeMillis() - CurrentTime >= 1000){
                        lblG7231BitRate.setText(TotalBits + "");
                        CurrentTime = System.currentTimeMillis();
                        TotalBits = 0;
                    }
                    if(CurrentAudioDecoder.Decode(result.Result, result, timestamp) == Codec_Errors.CODEC_SUCCEEDED){
                        sample = result.Result;
                    }
                }
            }
            
            if(CurrentAudioOutputDevice != null)
                CurrentAudioOutputDevice.Present(sample, 0);
            if(chkAudioDisplay.isSelected()) PresentAudio(sample);
            //AudioQueue.add(sample);
        }
    }
    
    private VideoInputDevice CurrentVideoInputDevice;
    private VideoMediaFormat CurrentVideoInputFormat;
    private VideoOutputDevice CurrentVideoOutputDevice;
    private AudioMediaFormat CurrentAudioInputFormat;
    private AudioInputDevice CurrentAudioInputDevice;
    private AudioOutputDevice CurrentAudioOutputDevice;
    private Codec CurrentVideoEncoder;
    private Codec CurrentVideoDecoder;
    private CodecData CurrentVideoCodecData;
    
    private Codec CurrentAudioEncoder;
    private Codec CurrentAudioDecoder;
    private CodecData CurrentAudioCodecData;
    
    /**
     * Creates new form MainForm
     */
    public MainForm() {
        initComponents();
        LoadVideoInputDevices();
        LoadAudioInputDevices();
        LoadAudioOutputDevices();
    }
    
    private void LoadVideoInputDevices(){
        VideoInputDevice maindevice = new VideoInputDevice(0,"");
        java.util.List<Device> devices = new ArrayList<Device>();
        Device_Errors err = maindevice.GetDevices(devices);
        
        if(err == Device_Errors.SUCCEEDED){
            DefaultListModel model = new DefaultListModel();
            for(int x = 0; x < devices.size(); x++){
                model.addElement(devices.get(x));
            }
            lstAvailableVideoInputDevices.setModel(model);
        }
    }
    
    private void LoadAudioInputDevices(){
        AudioInputDevice maindevice = new AudioInputDevice(0,"");
        java.util.List<Device> devices = new ArrayList<Device>();
        Device_Errors err = maindevice.GetDevices(devices);
        
        if(err == Device_Errors.SUCCEEDED){
            DefaultListModel model = new DefaultListModel();
            for(int x = 0; x < devices.size(); x++){
                model.addElement(devices.get(x));
            }
            lstAvailableAudioInputDevices.setModel(model);
        }
    }
    
    private void LoadAudioOutputDevices(){
        
    }
    
    private boolean OpenVideoInputDevice(){
        boolean retval = false;
        if(CurrentVideoInputDevice != null && CurrentVideoInputFormat != null){
            CurrentVideoInputDevice.Listener = new MyVideoDeviceListener();
//            VideoPixelFormat pix = VideoPixelFormat.ANY;
//            if(System.getProperty("os.name").toLowerCase().contains("lin")){
//                //String ver = System.getProperty("os.version");
//                //String os = System.getProperty("os.name");
//                pix = VideoPixelFormat.YUYV;
//            }
            //VideoMediaFormat vf = new VideoMediaFormat(Integer.parseInt(txtH263FPS.getText()), CurrentVideoInputFormat.Width, CurrentVideoInputFormat.Height, CurrentVideoInputFormat.PixelFormat);
            VideoMediaFormat vf = new VideoMediaFormat(Integer.parseInt(txtH263FPS.getText()), 320, 240, CurrentVideoInputFormat.PixelFormat);

            Device_Errors err = CurrentVideoInputDevice.Open(vf);
            if(err == Device_Errors.SUCCEEDED)
            {
                
                retval = true;
            }
            else{
                retval = CurrentVideoInputDevice.Open(vf) == Device_Errors.SUCCEEDED;
            }
        }
        return retval;
    }
    
    private boolean OpenVideoOutputDevice(){
        boolean retval = true;
        CurrentVideoOutputDevice = new VideoOutputDevice(0, "");
        int fps = CurrentVideoInputFormat.FPS;
        if(CurrentVideoInputFormat.FPS == 0){
            fps = 30;
        }
        //VideoMediaFormat vf = new VideoMediaFormat(fps, CurrentVideoInputFormat.Width, CurrentVideoInputFormat.Height, VideoPixelFormat.ANY);
        VideoMediaFormat vf = new VideoMediaFormat(fps, 320, 240, VideoPixelFormat.ANY);
        CurrentVideoOutputDevice.Open(vf, VideoView, false);
        return retval;
    }
    
    private boolean OpenVideoCodec(){
        boolean retval = true;
        CurrentVideoCodecData = new CodecData(Integer.parseInt(txtH263BitRate.getText()), 0,false,Integer.parseInt(txtH263FrameSpace.getText()),0);
        //VideoMediaFormat vf = new VideoMediaFormat(Integer.parseInt(txtH263FPS.getText()), CurrentVideoInputFormat.Width, CurrentVideoInputFormat.Height, VideoPixelFormat.RGB24);
        VideoMediaFormat vf = new VideoMediaFormat(Integer.parseInt(txtH263FPS.getText()), 320, 240, VideoPixelFormat.RGB24);
        CurrentVideoEncoder = new H263VideoEncoder();
        CurrentVideoDecoder = new H263VideoDecoder();
        Codec_Errors err = CurrentVideoEncoder.Open(vf, CurrentVideoCodecData);
        err = CurrentVideoDecoder.Open(vf, CurrentVideoCodecData);
        return err == Codec_Errors.CODEC_SUCCEEDED;
    }
    
    private boolean OpenAudioCodec(){
        boolean retval = true;
        if(TestAudioCodec.isSelected()){
            CurrentAudioCodecData = new CodecData(Integer.parseInt(cmbG7231BitRate.getSelectedItem().toString()), 0,false,0,0);
            CurrentAudioEncoder = new G7231AudioEncoder();
            CurrentAudioDecoder = new G7231AudioDecoder();
            Codec_Errors err = CurrentAudioEncoder.Open(CurrentAudioInputFormat, CurrentAudioCodecData);
            err = CurrentAudioDecoder.Open(CurrentAudioInputFormat, CurrentAudioCodecData);
            retval = err == Codec_Errors.CODEC_SUCCEEDED;
        }
        return retval;
    }
    
    private boolean CloseVideoInputDevice(){
        boolean retval = true;
        if(CurrentVideoInputDevice == null)
            retval = false;
        else if(CurrentVideoInputDevice.Close() != Device_Errors.SUCCEEDED)
            retval = false;
        //CurrentVideoInputDevice = null;
        return retval;
    }
    
    private boolean CloseVideoOutputDevice(){
        boolean retval = true;
        if(CurrentVideoOutputDevice != null){
            CurrentVideoOutputDevice.Close();
        }
        //CurrentVideoOutputDevice = null;
        return retval;
    }
    
    private boolean CloseVideoCodec(){
        boolean retval = true;
        if(CurrentVideoEncoder != null){
            CurrentVideoEncoder.Close();
        }
        if(CurrentVideoDecoder != null){
            CurrentVideoDecoder.Close();
        }
        CurrentVideoEncoder = null;
        CurrentVideoDecoder = null;
        return retval;
    }
    
    private boolean CloseAudioCodec(){
        boolean retval = true;
        if(CurrentAudioEncoder != null){
            CurrentAudioEncoder.Close();
        }
        if(CurrentAudioDecoder != null){
            CurrentAudioDecoder.Close();
        }
        CurrentAudioEncoder = null;
        CurrentAudioDecoder = null;
        return retval;
    }
    
    private boolean RunVideoTest(){
        boolean retval = true;
        if(TestVideoCodec.isSelected()){
           retval = retval && OpenVideoCodec();
        }
        if(retval)
            retval = retval && OpenVideoOutputDevice();
        if(retval)
            retval = retval && OpenVideoInputDevice();
        return retval;
    }
    
    private void PresentAudio(byte[] samples){
        int ssize = (CurrentAudioInputFormat.BitsPerSample / 8);
        int channels = CurrentAudioInputFormat.Channels;
        int width = AudioView.getWidth();
        int height = AudioView.getHeight();
        long ymax = (long) Math.pow(2,(double)ssize*8);
        double xscale = (double)width / (double)samples.length*2;
        double yscale = (double)height / (double)ymax*2;
        
        java.awt.image.BufferedImage graph = new java.awt.image.BufferedImage(AudioView.getWidth(), AudioView.getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D g = graph.createGraphics();
        g.setColor(Color.white);
        g.fillRect(0,0,width,height);
        g.setColor(Color.blue);
        g.drawLine(0, (int)((ymax/2) * yscale), width, (int)((ymax/2) * yscale));
        
        int plX = 0;
        int plY = 0;
        int slX = 0;
        int slY = 0;
        try{
            DataInputStream input = new DataInputStream(new ByteArrayInputStream(samples));
            for(int i = 0; i < samples.length; i+=(ssize*channels)){
                long[] csamples = new long[channels];
                for(int c = 0; c < channels; c++){
                    switch(ssize)
                    {
                        case 1:
                            csamples[c] = input.readByte();
                            break;
                        case 2:
                            csamples[c] = input.readShort();
                            break;
                        case 4:
                            csamples[c] = input.readInt();
                    }
                    if(csamples[c] < 0)
                        csamples[c] = (ymax/2) + csamples[c];
                }
                int x = i / (ssize * channels);
                x *= xscale;
                
                int y = (int)(csamples[0] * yscale);
                g.setColor(Color.red);
                g.drawLine(plX, plY, x, y);
                plX = x;
                plY = y;
                g.setColor(Color.green);
                if(csamples.length == 2){
                    y = (int)(csamples[1] * yscale);
                    g.drawLine(slX, slY, x, y);
                    slX = x;
                    slY = y;
                }
            }
        }
        catch(Exception e){}
        Graphics2D g2 = (Graphics2D)AudioView.getGraphics();
        g2.drawImage(graph, 0,0,null);
    }
    
    private boolean OpenAudioInputDevice(){
        boolean retval = true;
        if(CurrentAudioInputDevice == null)
            retval = false;
        else if(CurrentAudioInputFormat == null)
            retval = false;
        else
        {
            AudioQueue.clear();
            CurrentAudioInputDevice.Listener = new MyAudioDeviceListener();
            ActionListener l = new ActionListener(){
                public void actionPerformed(ActionEvent evt){
                    if(AudioQueue.size() > 0)
                    {
                        byte[] sample = AudioQueue.remove();
                        if(CurrentAudioOutputDevice != null)
                            CurrentAudioOutputDevice.Present(sample, 0);
                        if(chkAudioDisplay.isSelected()) PresentAudio(sample);
                    }
                }
            };
            double time = (double)CurrentAudioInputFormat.SampleRate/240*0.75;
            AudioTimer = new javax.swing.Timer((int)time, l);
            //AudioTimer.start();
            CurrentAudioInputDevice.Open(CurrentAudioInputFormat);
        }
        return retval;
    }
    
    private boolean CloseAudioInputDevice(){
        boolean retval = true;
        if(CurrentAudioInputDevice != null)
        {
            CurrentAudioInputDevice.Close();
        }
        if(AudioTimer != null){
            AudioTimer.stop();
            AudioTimer = null;
            AudioQueue.clear();
        }
        return retval;
    }
    
    private boolean OpenAudioOutputDevice(){
        boolean retval = true;
        if(CurrentAudioInputFormat == null){
            retval = false;
        }
        else{
            CurrentAudioOutputDevice = new AudioOutputDevice(Integer.parseInt(AudioOutDeviceIndex.getText()),"");
            retval = CurrentAudioOutputDevice.Open(CurrentAudioInputFormat) == Device_Errors.SUCCEEDED;
        }
        return retval;
    }
    
    private void CloseAudioOutputDevice(){
        if(CurrentAudioOutputDevice != null){
            CurrentAudioOutputDevice.Close();
            CurrentAudioOutputDevice = null;
        }
    }
    
    private boolean RunAudioTest(){
        return OpenAudioOutputDevice() && OpenAudioInputDevice() && OpenAudioCodec();
    }

    /**
     * This method is called from within the constructor to initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is always
     * regenerated by the Form Editor.
     */
    @SuppressWarnings("unchecked")
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        jSplitPane1 = new javax.swing.JSplitPane();
        jPanel1 = new javax.swing.JPanel();
        jTabbedPane1 = new javax.swing.JTabbedPane();
        jPanel3 = new javax.swing.JPanel();
        jPanel9 = new javax.swing.JPanel();
        jScrollPane1 = new javax.swing.JScrollPane();
        lstAvailableVideoInputDevices = new javax.swing.JList();
        jPanel10 = new javax.swing.JPanel();
        jScrollPane2 = new javax.swing.JScrollPane();
        lstAvailableVideoInputFormats = new javax.swing.JList();
        jPanel4 = new javax.swing.JPanel();
        jPanel13 = new javax.swing.JPanel();
        jScrollPane3 = new javax.swing.JScrollPane();
        lstAvailableAudioInputDevices = new javax.swing.JList();
        jPanel15 = new javax.swing.JPanel();
        jScrollPane4 = new javax.swing.JScrollPane();
        lstAvailableAudioInputFormats = new javax.swing.JList();
        jPanel6 = new javax.swing.JPanel();
        chkAudioDisplay = new javax.swing.JCheckBox();
        jLabel5 = new javax.swing.JLabel();
        AudioOutDeviceIndex = new javax.swing.JTextField();
        jPanel7 = new javax.swing.JPanel();
        jLabel1 = new javax.swing.JLabel();
        txtH263BitRate = new javax.swing.JTextField();
        jLabel2 = new javax.swing.JLabel();
        txtH263FPS = new javax.swing.JTextField();
        jLabel3 = new javax.swing.JLabel();
        txtH263FrameSpace = new javax.swing.JTextField();
        lblH263BitRate = new javax.swing.JLabel();
        lblH263FrameRate = new javax.swing.JLabel();
        jPanel8 = new javax.swing.JPanel();
        jLabel4 = new javax.swing.JLabel();
        cmbG7231BitRate = new javax.swing.JComboBox();
        lblG7231BitRate = new javax.swing.JLabel();
        jPanel2 = new javax.swing.JPanel();
        jPanel11 = new javax.swing.JPanel();
        TestVideo = new javax.swing.JCheckBox();
        TestVideoCodec = new javax.swing.JCheckBox();
        TestAudio = new javax.swing.JCheckBox();
        TestAudioCodec = new javax.swing.JCheckBox();
        btnRun = new javax.swing.JButton();
        btnStop = new javax.swing.JButton();
        RecordToFile = new javax.swing.JCheckBox();
        jButton1 = new javax.swing.JButton();
        jPanel12 = new javax.swing.JPanel();
        VideoView = new javax.swing.JPanel();
        AudioView = new javax.swing.JPanel();

        setDefaultCloseOperation(javax.swing.WindowConstants.EXIT_ON_CLOSE);

        jSplitPane1.setDividerLocation(300);

        jPanel1.setBorder(javax.swing.BorderFactory.createTitledBorder("Configuration"));
        jPanel1.setPreferredSize(new java.awt.Dimension(300, 300));
        jPanel1.setLayout(new java.awt.BorderLayout());

        jPanel9.setBorder(javax.swing.BorderFactory.createTitledBorder("Available Devices"));
        jPanel9.setLayout(new java.awt.BorderLayout());

        lstAvailableVideoInputDevices.setModel(new javax.swing.AbstractListModel() {
            String[] strings = { "Item 1", "Item 2", "Item 3", "Item 4", "Item 5" };
            public int getSize() { return strings.length; }
            public Object getElementAt(int i) { return strings[i]; }
        });
        lstAvailableVideoInputDevices.addListSelectionListener(new javax.swing.event.ListSelectionListener() {
            public void valueChanged(javax.swing.event.ListSelectionEvent evt) {
                lstAvailableVideoInputDevicesValueChanged(evt);
            }
        });
        jScrollPane1.setViewportView(lstAvailableVideoInputDevices);

        jPanel9.add(jScrollPane1, java.awt.BorderLayout.CENTER);

        jPanel10.setBorder(javax.swing.BorderFactory.createTitledBorder("Available Formats"));
        jPanel10.setLayout(new java.awt.BorderLayout());

        lstAvailableVideoInputFormats.setModel(new javax.swing.AbstractListModel() {
            String[] strings = { "Item 1", "Item 2", "Item 3", "Item 4", "Item 5" };
            public int getSize() { return strings.length; }
            public Object getElementAt(int i) { return strings[i]; }
        });
        lstAvailableVideoInputFormats.addListSelectionListener(new javax.swing.event.ListSelectionListener() {
            public void valueChanged(javax.swing.event.ListSelectionEvent evt) {
                lstAvailableVideoInputFormatsValueChanged(evt);
            }
        });
        jScrollPane2.setViewportView(lstAvailableVideoInputFormats);

        jPanel10.add(jScrollPane2, java.awt.BorderLayout.PAGE_START);

        javax.swing.GroupLayout jPanel3Layout = new javax.swing.GroupLayout(jPanel3);
        jPanel3.setLayout(jPanel3Layout);
        jPanel3Layout.setHorizontalGroup(
            jPanel3Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(jPanel9, javax.swing.GroupLayout.DEFAULT_SIZE, 303, Short.MAX_VALUE)
            .addComponent(jPanel10, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
        );
        jPanel3Layout.setVerticalGroup(
            jPanel3Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel3Layout.createSequentialGroup()
                .addComponent(jPanel9, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(jPanel10, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(0, 0, Short.MAX_VALUE))
        );

        jTabbedPane1.addTab("Video In", jPanel3);

        jPanel13.setBorder(javax.swing.BorderFactory.createTitledBorder("Audio Devices"));
        jPanel13.setPreferredSize(new java.awt.Dimension(282, 200));
        jPanel13.setLayout(new java.awt.BorderLayout());

        lstAvailableAudioInputDevices.setModel(new javax.swing.AbstractListModel() {
            String[] strings = { "Item 1", "Item 2", "Item 3", "Item 4", "Item 5" };
            public int getSize() { return strings.length; }
            public Object getElementAt(int i) { return strings[i]; }
        });
        lstAvailableAudioInputDevices.addListSelectionListener(new javax.swing.event.ListSelectionListener() {
            public void valueChanged(javax.swing.event.ListSelectionEvent evt) {
                lstAvailableAudioInputDevicesValueChanged(evt);
            }
        });
        jScrollPane3.setViewportView(lstAvailableAudioInputDevices);

        jPanel13.add(jScrollPane3, java.awt.BorderLayout.CENTER);

        jPanel4.add(jPanel13);

        jPanel15.setBorder(javax.swing.BorderFactory.createTitledBorder("Formats"));
        jPanel15.setPreferredSize(new java.awt.Dimension(282, 200));
        jPanel15.setLayout(new java.awt.BorderLayout());

        lstAvailableAudioInputFormats.setModel(new javax.swing.AbstractListModel() {
            String[] strings = { "Item 1", "Item 2", "Item 3", "Item 4", "Item 5" };
            public int getSize() { return strings.length; }
            public Object getElementAt(int i) { return strings[i]; }
        });
        lstAvailableAudioInputFormats.addListSelectionListener(new javax.swing.event.ListSelectionListener() {
            public void valueChanged(javax.swing.event.ListSelectionEvent evt) {
                lstAvailableAudioInputFormatsValueChanged(evt);
            }
        });
        jScrollPane4.setViewportView(lstAvailableAudioInputFormats);

        jPanel15.add(jScrollPane4, java.awt.BorderLayout.CENTER);

        jPanel4.add(jPanel15);

        jTabbedPane1.addTab("Audio In", jPanel4);

        chkAudioDisplay.setText("Visually Display Audio");
        jPanel6.add(chkAudioDisplay);

        jLabel5.setText("Audio Device");
        jPanel6.add(jLabel5);

        AudioOutDeviceIndex.setText("0");
        jPanel6.add(AudioOutDeviceIndex);

        jTabbedPane1.addTab("Audio Out", jPanel6);

        jLabel1.setText("Codec Bit Rate");

        txtH263BitRate.setText("128000");

        jLabel2.setText("Frame Rate");

        txtH263FPS.setText("15");

        jLabel3.setText("Frame Space");

        txtH263FrameSpace.setText("160");

        lblH263BitRate.setText("Actual");

        lblH263FrameRate.setText("Actual");

        javax.swing.GroupLayout jPanel7Layout = new javax.swing.GroupLayout(jPanel7);
        jPanel7.setLayout(jPanel7Layout);
        jPanel7Layout.setHorizontalGroup(
            jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel7Layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING, false)
                    .addGroup(jPanel7Layout.createSequentialGroup()
                        .addComponent(jLabel1)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addComponent(txtH263BitRate, javax.swing.GroupLayout.PREFERRED_SIZE, 54, javax.swing.GroupLayout.PREFERRED_SIZE))
                    .addGroup(jPanel7Layout.createSequentialGroup()
                        .addComponent(jLabel2)
                        .addGap(18, 18, 18)
                        .addComponent(txtH263FPS))
                    .addGroup(jPanel7Layout.createSequentialGroup()
                        .addComponent(jLabel3)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addComponent(txtH263FrameSpace)))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(lblH263BitRate)
                    .addComponent(lblH263FrameRate))
                .addContainerGap(68, Short.MAX_VALUE))
        );
        jPanel7Layout.setVerticalGroup(
            jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel7Layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jLabel1)
                    .addComponent(txtH263BitRate, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(lblH263BitRate))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jLabel2)
                    .addComponent(txtH263FPS, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(lblH263FrameRate))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addGroup(jPanel7Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jLabel3)
                    .addComponent(txtH263FrameSpace, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                .addContainerGap(405, Short.MAX_VALUE))
        );

        jTabbedPane1.addTab("H.263", jPanel7);

        jLabel4.setText("Bitrate");

        cmbG7231BitRate.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "6300", "5600" }));

        lblG7231BitRate.setText("Actual");

        javax.swing.GroupLayout jPanel8Layout = new javax.swing.GroupLayout(jPanel8);
        jPanel8.setLayout(jPanel8Layout);
        jPanel8Layout.setHorizontalGroup(
            jPanel8Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel8Layout.createSequentialGroup()
                .addContainerGap()
                .addComponent(jLabel4)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(cmbG7231BitRate, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(lblG7231BitRate)
                .addContainerGap(105, Short.MAX_VALUE))
        );
        jPanel8Layout.setVerticalGroup(
            jPanel8Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel8Layout.createSequentialGroup()
                .addContainerGap()
                .addGroup(jPanel8Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jLabel4)
                    .addComponent(cmbG7231BitRate, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(lblG7231BitRate))
                .addContainerGap(473, Short.MAX_VALUE))
        );

        jTabbedPane1.addTab("G.723.1", jPanel8);

        jPanel1.add(jTabbedPane1, java.awt.BorderLayout.CENTER);

        jSplitPane1.setLeftComponent(jPanel1);

        jPanel2.setPreferredSize(new java.awt.Dimension(300, 300));
        jPanel2.setLayout(new java.awt.BorderLayout());

        jPanel11.setBorder(javax.swing.BorderFactory.createTitledBorder("Actions"));

        TestVideo.setText("Test Video");

        TestVideoCodec.setText("Use Video Codec");

        TestAudio.setText("Test Audio");

        TestAudioCodec.setText("Test Audio Codec");

        btnRun.setText("Run");
        btnRun.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                btnRunActionPerformed(evt);
            }
        });

        btnStop.setText("Stop");
        btnStop.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                btnStopActionPerformed(evt);
            }
        });

        RecordToFile.setText("Record To File");

        jButton1.setLabel("Reload Devices");
        jButton1.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jButton1ActionPerformed(evt);
            }
        });

        javax.swing.GroupLayout jPanel11Layout = new javax.swing.GroupLayout(jPanel11);
        jPanel11.setLayout(jPanel11Layout);
        jPanel11Layout.setHorizontalGroup(
            jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel11Layout.createSequentialGroup()
                .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addGroup(jPanel11Layout.createSequentialGroup()
                        .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                            .addComponent(TestVideo)
                            .addComponent(TestAudio))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                            .addComponent(TestAudioCodec)
                            .addComponent(TestVideoCodec)))
                    .addGroup(jPanel11Layout.createSequentialGroup()
                        .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                            .addGroup(jPanel11Layout.createSequentialGroup()
                                .addComponent(btnRun)
                                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(btnStop))
                            .addComponent(RecordToFile))
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                        .addComponent(jButton1)))
                .addGap(0, 35, Short.MAX_VALUE))
        );
        jPanel11Layout.setVerticalGroup(
            jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(jPanel11Layout.createSequentialGroup()
                .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(TestVideo)
                    .addComponent(TestVideoCodec))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(TestAudio)
                    .addComponent(TestAudioCodec))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                .addGroup(jPanel11Layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(btnRun)
                    .addComponent(btnStop)
                    .addComponent(jButton1))
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED, 6, Short.MAX_VALUE)
                .addComponent(RecordToFile))
        );

        jPanel2.add(jPanel11, java.awt.BorderLayout.PAGE_START);

        jPanel12.setBorder(javax.swing.BorderFactory.createTitledBorder("View"));
        jPanel12.setLayout(new java.awt.BorderLayout());

        VideoView.setBorder(javax.swing.BorderFactory.createTitledBorder("Video"));
        VideoView.setPreferredSize(new java.awt.Dimension(320, 240));

        javax.swing.GroupLayout VideoViewLayout = new javax.swing.GroupLayout(VideoView);
        VideoView.setLayout(VideoViewLayout);
        VideoViewLayout.setHorizontalGroup(
            VideoViewLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 240, Short.MAX_VALUE)
        );
        VideoViewLayout.setVerticalGroup(
            VideoViewLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 320, Short.MAX_VALUE)
        );

        jPanel12.add(VideoView, java.awt.BorderLayout.CENTER);

        AudioView.setBorder(javax.swing.BorderFactory.createTitledBorder("Audio"));

        javax.swing.GroupLayout AudioViewLayout = new javax.swing.GroupLayout(AudioView);
        AudioView.setLayout(AudioViewLayout);
        AudioViewLayout.setHorizontalGroup(
            AudioViewLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 240, Short.MAX_VALUE)
        );
        AudioViewLayout.setVerticalGroup(
            AudioViewLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGap(0, 90, Short.MAX_VALUE)
        );

        jPanel12.add(AudioView, java.awt.BorderLayout.PAGE_START);

        jPanel2.add(jPanel12, java.awt.BorderLayout.CENTER);

        jSplitPane1.setRightComponent(jPanel2);

        getContentPane().add(jSplitPane1, java.awt.BorderLayout.CENTER);

        pack();
    }// </editor-fold>//GEN-END:initComponents

    private void btnRunActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnRunActionPerformed
        if(RecordToFile.isSelected()){
            
        }
        
        if(TestVideo.isSelected())
        {
            
            boolean ran = RunVideoTest();
            if(!ran)
            {
                //let the user know
            }
        }
        if(TestAudio.isSelected()){
            boolean ran = RunAudioTest();
        }
        
        if(RecordToFile.isSelected() && CurrentAudioInputFormat != null && CurrentVideoInputFormat != null){
            FileOutput = new FileOutputDevice(0, "MyFile");
            String file = System.getProperty("user.dir");
            String sep = System.getProperty("file.separator");
            if(!file.endsWith(sep)){
                file += sep;
            }
            file += "Desktop" + sep + "test.wmv";
            System.out.println("Opening " + file + " with the following formats " + CurrentVideoInputFormat.toString() + " " + CurrentAudioInputFormat.toString());
            FileMediaFormat fileFormat = new FileMediaFormat(file, CurrentVideoInputFormat.Width, CurrentVideoInputFormat.Height, CurrentAudioInputFormat.SampleRate, CurrentAudioInputFormat.BitsPerSample, CurrentAudioInputFormat.Channels);
            FileOutput.Open(fileFormat);
        }
        
    }//GEN-LAST:event_btnRunActionPerformed

    private void btnStopActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_btnStopActionPerformed
        CloseVideoInputDevice();
        CloseVideoOutputDevice();
        CloseVideoCodec();
        
        CloseAudioInputDevice();
        CloseAudioOutputDevice();
        if(FileOutput != null){
            FileOutput.Close();
            FileOutput = null;
        }
        
    }//GEN-LAST:event_btnStopActionPerformed

    private void lstAvailableAudioInputFormatsValueChanged(javax.swing.event.ListSelectionEvent evt) {//GEN-FIRST:event_lstAvailableAudioInputFormatsValueChanged
        AudioMediaFormat format = (AudioMediaFormat) lstAvailableAudioInputFormats.getSelectedValue();
        if(format.SampleRate < 0){
            CurrentAudioInputFormat = new AudioMediaFormat(format.BitsPerSample, format.Channels, 8000);
        }
        else{
            CurrentAudioInputFormat = format;
        }
        
    }//GEN-LAST:event_lstAvailableAudioInputFormatsValueChanged

    private void lstAvailableAudioInputDevicesValueChanged(javax.swing.event.ListSelectionEvent evt) {//GEN-FIRST:event_lstAvailableAudioInputDevicesValueChanged
        AudioInputDevice device = (AudioInputDevice)lstAvailableAudioInputDevices.getSelectedValue();
        if(device != null){
            DefaultListModel model = new DefaultListModel();
            for(int x = 0; x < device.Formats.size(); x++){
                model.addElement(device.Formats.get(x));
            }
            lstAvailableAudioInputFormats.setModel(model);
            CurrentAudioInputDevice = device;
        }
    }//GEN-LAST:event_lstAvailableAudioInputDevicesValueChanged

    private void lstAvailableVideoInputFormatsValueChanged(javax.swing.event.ListSelectionEvent evt) {//GEN-FIRST:event_lstAvailableVideoInputFormatsValueChanged
        VideoMediaFormat format = (VideoMediaFormat) lstAvailableVideoInputFormats.getSelectedValue();
        CurrentVideoInputFormat = format;
    }//GEN-LAST:event_lstAvailableVideoInputFormatsValueChanged

    private void lstAvailableVideoInputDevicesValueChanged(javax.swing.event.ListSelectionEvent evt) {//GEN-FIRST:event_lstAvailableVideoInputDevicesValueChanged
        VideoInputDevice device = (VideoInputDevice)lstAvailableVideoInputDevices.getSelectedValue();
        if(device != null){
            DefaultListModel model = new DefaultListModel();
            for(int x = 0; x < device.Formats.size(); x++){
                model.addElement(device.Formats.get(x));
            }
            lstAvailableVideoInputFormats.setModel(model);
            CurrentVideoInputDevice = device;
        }
    }//GEN-LAST:event_lstAvailableVideoInputDevicesValueChanged

    private void jButton1ActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jButton1ActionPerformed
        LoadVideoInputDevices();
    }//GEN-LAST:event_jButton1ActionPerformed

    
    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JTextField AudioOutDeviceIndex;
    private javax.swing.JPanel AudioView;
    private javax.swing.JCheckBox RecordToFile;
    private javax.swing.JCheckBox TestAudio;
    private javax.swing.JCheckBox TestAudioCodec;
    private javax.swing.JCheckBox TestVideo;
    private javax.swing.JCheckBox TestVideoCodec;
    private javax.swing.JPanel VideoView;
    private javax.swing.JButton btnRun;
    private javax.swing.JButton btnStop;
    private javax.swing.JCheckBox chkAudioDisplay;
    private javax.swing.JComboBox cmbG7231BitRate;
    private javax.swing.JButton jButton1;
    private javax.swing.JLabel jLabel1;
    private javax.swing.JLabel jLabel2;
    private javax.swing.JLabel jLabel3;
    private javax.swing.JLabel jLabel4;
    private javax.swing.JLabel jLabel5;
    private javax.swing.JPanel jPanel1;
    private javax.swing.JPanel jPanel10;
    private javax.swing.JPanel jPanel11;
    private javax.swing.JPanel jPanel12;
    private javax.swing.JPanel jPanel13;
    private javax.swing.JPanel jPanel15;
    private javax.swing.JPanel jPanel2;
    private javax.swing.JPanel jPanel3;
    private javax.swing.JPanel jPanel4;
    private javax.swing.JPanel jPanel6;
    private javax.swing.JPanel jPanel7;
    private javax.swing.JPanel jPanel8;
    private javax.swing.JPanel jPanel9;
    private javax.swing.JScrollPane jScrollPane1;
    private javax.swing.JScrollPane jScrollPane2;
    private javax.swing.JScrollPane jScrollPane3;
    private javax.swing.JScrollPane jScrollPane4;
    private javax.swing.JSplitPane jSplitPane1;
    private javax.swing.JTabbedPane jTabbedPane1;
    private javax.swing.JLabel lblG7231BitRate;
    private javax.swing.JLabel lblH263BitRate;
    private javax.swing.JLabel lblH263FrameRate;
    private javax.swing.JList lstAvailableAudioInputDevices;
    private javax.swing.JList lstAvailableAudioInputFormats;
    private javax.swing.JList lstAvailableVideoInputDevices;
    private javax.swing.JList lstAvailableVideoInputFormats;
    private javax.swing.JTextField txtH263BitRate;
    private javax.swing.JTextField txtH263FPS;
    private javax.swing.JTextField txtH263FrameSpace;
    // End of variables declaration//GEN-END:variables
}
