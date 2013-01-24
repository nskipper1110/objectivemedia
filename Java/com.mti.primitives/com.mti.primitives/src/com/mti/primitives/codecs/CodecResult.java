/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package com.mti.primitives.codecs;

/**
 *
 * @author nathan
 */
public class CodecResult {
    public byte[] Result;
    public long Timestamp;
    
    public void SetResult(byte[] result, long timestamp){
        Result = result;
        Timestamp = timestamp;
    }
}
