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
#include "platform_includes.h"
#include "platform_codecs_defs.h"
#include <math.h>

/***********************************************************************************************************************
Description: The H263VideoEncoder class is a subclass of the Codec class which implements the encoding functionality for
H.263.
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Creation Date: 11/28/2012
Revision History:
1.0.0 - Initial Creation
*************************************************************************************************************************/
class H263VideoEncoder : public Codec{
public:
	/*********************************************************************************************
	Instantiates a new H263VideoEncoder object.
	**********************************************************************************************/
	H263VideoEncoder();
	/*********************************************************************************************
	Opens the underlying primitives and prepares the object for encoding.
	Parameters:
	encFormat - Should be a VideoMediaFormat object that describes the format of the incoming video frames.
	encData - A CodecData object which provides codec information, such as bit rate and so on.
	**********************************************************************************************/
	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	/********************************************************************************************
	Closes the encoder primitives and frees all memory used by the object.
	*********************************************************************************************/
	Codec_Errors Close();
	/********************************************************************************************
	Encodes the provided sample into an H.263 packet.
	Parameters:
	inSample - a pointer to the memory space containing the video frame to be encoded.
	insize - The size, in bytes, of the memory space containing the video frame to be encoded.
	outSample - A reference to a pointer that will receive the encoded frame.
	outsize - A reference to an integer that will receive the size of the encoded frame memory space.
	timestamp - The timestamp reference for when the frame was captured, not used.
	*********************************************************************************************/
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Decoding is not supported by this class, so this function always returns "NOT_SUPPORTED".
	*********************************************************************************************/
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Destroys the object.
	*********************************************************************************************/
	~H263VideoEncoder();
protected:
};

/***********************************************************************************************************************
Description: The H263VideoDecoder class is a subclass of the Codec class which implements the decoding functionality for
H.263.
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Creation Date: 11/28/2012
Revision History:
1.0.0 - Initial Creation
*************************************************************************************************************************/
class H263VideoDecoder : public Codec{
public:
	/*********************************************************************************************
	Instantiates a new H263VideoDecoder object.
	**********************************************************************************************/
	H263VideoDecoder();
	/*********************************************************************************************
	Opens the underlying primitives and prepares the object for decoding. The H.263 decoder does not
	need any configuration parameters to decode incoming packets, therefore the encData parameter is not
	used. The encFormat parameter is used to "scale" the decoded frame to a desired output format.
	Parameters:
	encFormat - Should be a VideoMediaFormat object that describes the format in which the caller wishes
		to receive decoded frames.
	encData - A CodecData object which provides codec information, such as bit rate and so on. Not used.
		Should be instantiated, but isn't required to have any values set.
	**********************************************************************************************/
	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	/********************************************************************************************
	Closes the decoder primitives and frees all memory used by the object.
	*********************************************************************************************/
	Codec_Errors Close();
	/********************************************************************************************
	Encoding is not supported by this class, so this function always returns "NOT_SUPPORTED".
	*********************************************************************************************/
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Decodes the provided sample frame an H.263 packet into a bitmap frame described by the 
	video format provided in the Open function call.
	Parameters:
	inSample - a pointer to the memory space containing the H.263 video frame to be decoded.
	insize - The size, in bytes, of the memory space containing the video frame to be decoded.
	outSample - A reference to a pointer that will receive the decoded frame.
	outsize - A reference to an integer that will receive the size of the frame memory space.
	timestamp - The timestamp reference for when the frame was captured, not used.
	*********************************************************************************************/
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Destroys the object.
	*********************************************************************************************/
	~H263VideoDecoder();
protected:
};

/***********************************************************************************************************************
Description: The VC1VideoDecoder class is a subclass of the Codec class which implements the decoding functionality for
VC-1/WMV9 main profile. This decoder only supports main profile VBR decoding at the moment.
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Creation Date: 11/28/2012
Revision History:
1.0.0 - Initial Creation
*************************************************************************************************************************/
class VC1VideoDecoder : public Codec{
public:
	/*********************************************************************************************
	Instantiates a new VC1VideoDecoder object.
	**********************************************************************************************/
	VC1VideoDecoder();
	/*********************************************************************************************
	Opens the underlying primitives and prepares the object for decoding.
	Parameters:
	encFormat - Should be a VideoMediaFormat object that describes the format in which the caller wishes
		to receive decoded frames.
	encData - A CodecData object which provides codec information, such as bit rate and so on. Not used.
		Should be instantiated, but isn't required to have any values set.
	**********************************************************************************************/
	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	/********************************************************************************************
	Closes the decoder primitives and frees all memory used by the object.
	*********************************************************************************************/
	Codec_Errors Close();
	/********************************************************************************************
	Encoding is not supported by this class, so this function always returns "NOT_SUPPORTED".
	*********************************************************************************************/
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Decodes the provided sample frame an VC-1 packet into a bitmap frame described by the 
	video format provided in the Open function call.
	Parameters:
	inSample - a pointer to the memory space containing the VC-1 video frame to be decoded.
	insize - The size, in bytes, of the memory space containing the video frame to be decoded.
	outSample - A reference to a pointer that will receive the decoded frame.
	outsize - A reference to an integer that will receive the size of the frame memory space.
	timestamp - The timestamp reference for when the frame was captured, not used.
	*********************************************************************************************/
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Destroys the object.
	*********************************************************************************************/
	~VC1VideoDecoder();
protected:
};

/***********************************************************************************************************************
Description: The G7231AudioEncoder class is a subclass of the Codec class which implements the encoding functionality for
G.723.1
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Creation Date: 11/28/2012
Revision History:
1.0.0 - Initial Creation
*************************************************************************************************************************/
class G7231AudioEncoder : public Codec{
public:
	/*********************************************************************************************
	Instantiates a new G7231AudioEncoder object.
	**********************************************************************************************/
	G7231AudioEncoder();
	/*********************************************************************************************
	Opens the underlying primitives and prepares the object for encoding.
	Parameters:
	encFormat - Should be a AudioMediaFormat object that describes the format of the incoming Audio samples.
	encData - A CodecData object which provides codec information, such as bit rate and so on.
	**********************************************************************************************/
	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	/********************************************************************************************
	Closes the encoder primitives and frees all memory used by the object.
	*********************************************************************************************/
	Codec_Errors Close();
	/********************************************************************************************
	Encodes the provided sample into an G.723.1 packet.
	Parameters:
	inSample - a pointer to the memory space containing the Audio frame to be encoded.
	insize - The size, in bytes, of the memory space containing the Audio samples to be encoded.
	outSample - A reference to a pointer that will receive the encoded frame.
	outsize - A reference to an integer that will receive the size of the encoded sample memory space.
	timestamp - The timestamp reference for when the sample was captured, not used.
	*********************************************************************************************/
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Decoding is not supported by this class, so this function always returns "NOT_SUPPORTED".
	*********************************************************************************************/
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Destroys the object.
	*********************************************************************************************/
	~G7231AudioEncoder();
protected:
};

/***********************************************************************************************************************
Description: The G7231AudioDecoder class is a subclass of the Codec class which implements the decoding functionality for
G.723.1
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Creation Date: 12/10/2012
Revision History:
1.0.0 - Initial Creation
*************************************************************************************************************************/
class G7231AudioDecoder : public Codec{
public:
	/*********************************************************************************************
	Instantiates a new G7231AudioDecoder object.
	**********************************************************************************************/
	G7231AudioDecoder();
	/*********************************************************************************************
	Opens the underlying primitives and prepares the object for encoding.
	Parameters:
	encFormat - Should be a AudioMediaFormat object that describes the format of the incoming Audio samples.
	encData - A CodecData object which provides codec information, such as bit rate and so on.
	**********************************************************************************************/
	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	/********************************************************************************************
	Closes the Decoder primitives and frees all memory used by the object.
	*********************************************************************************************/
	Codec_Errors Close();
	
	/********************************************************************************************
	Encoding is not supported by this class, so this function always returns "NOT_SUPPORTED".
	*********************************************************************************************/
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	
	/********************************************************************************************
	Decodes the G.723.1 packet into an array of audio samples.
	Parameters:
	inSample - a pointer to the memory space containing the G.723.1 packet to be decoded.
	insize - The size, in bytes, of the memory space containing the G.723.1 data.
	outSample - A reference to a pointer that will receive the decoded samples.
	outsize - A reference to an integer that will receive the size of the decoded samples memory space.
	timestamp - The timestamp reference for when the sample was captured, not used.
	*********************************************************************************************/
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Destroys the object.
	*********************************************************************************************/
	~G7231AudioDecoder();
protected:
};

/***********************************************************************************************************************
Description: The H264VideoDecoder class is a subclass of the Codec class which implements the decoding functionality for
H.264.
Author: Nathan Skipper, Montgomery Technology, Inc. (nathan@montgomerytechnology.com)
Creation Date: 10/29/2018
Revision History:
1.0.0 - Initial Creation
*************************************************************************************************************************/
class H264VideoDecoder : public Codec{
public:
	/*********************************************************************************************
	Instantiates a new H264VideoDecoder object.
	**********************************************************************************************/
	H264VideoDecoder();
	/*********************************************************************************************
	Opens the underlying primitives and prepares the object for decoding. The H.263 decoder does not
	need any configuration parameters to decode incoming packets, therefore the encData parameter is not
	used. The encFormat parameter is used to "scale" the decoded frame to a desired output format.
	Parameters:
	encFormat - Should be a VideoMediaFormat object that describes the format in which the caller wishes
		to receive decoded frames.
	encData - A CodecData object which provides codec information, such as bit rate and so on. Not used.
		Should be instantiated, but isn't required to have any values set.
	**********************************************************************************************/
	Codec_Errors Open(MediaFormat* encFormat, CodecData* encData);
	/********************************************************************************************
	Closes the decoder primitives and frees all memory used by the object.
	*********************************************************************************************/
	Codec_Errors Close();
	/********************************************************************************************
	Encoding is not supported by this class, so this function always returns "NOT_SUPPORTED".
	*********************************************************************************************/
	Codec_Errors Encode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Decodes the provided sample frame an H.263 packet into a bitmap frame described by the 
	video format provided in the Open function call.
	Parameters:
	inSample - a pointer to the memory space containing the H.263 video frame to be decoded.
	insize - The size, in bytes, of the memory space containing the video frame to be decoded.
	outSample - A reference to a pointer that will receive the decoded frame.
	outsize - A reference to an integer that will receive the size of the frame memory space.
	timestamp - The timestamp reference for when the frame was captured, not used.
	*********************************************************************************************/
	Codec_Errors Decode(void* inSample, long insize, void** outSample, long* outsize, long long timestamp);
	/********************************************************************************************
	Destroys the object.
	*********************************************************************************************/
	~H264VideoDecoder();
protected:
};