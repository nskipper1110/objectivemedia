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
#include "../stdafx.h"
#include "platform_devices.h"
#include <dshow.h>
#include <strmif.h>
#include <uuids.h>
#include <dshowasf.h>
#include "qedit.h"
#include <Dmodshow.h>
#include <stdio.h>
#include "CMediaBuffer.h"
#include <queue>
#include "macros.h"
#include "dxgrabber.h"
#include "fourcc.h"
#include <MMSystem.h>
/********************************************
Windows Specific Structures and functions
********************************************/
char * __stdcall ConvertBSTRToString(BSTR bstr) 
{ 
	const unsigned int stringLength = lstrlenW(bstr); 
	char *const ascii = new char [stringLength + 1]; 

	wcstombs(ascii, bstr, stringLength + 1); 

	return ascii; 
} 

typedef struct VideoInputDeviceContext{
	IGraphBuilder* Graph;
	ICaptureGraphBuilder2* Builder;
	IBaseFilter* CaptureFilter;
	IMediaControl* MediaControl;
	IVideoWindow* VideoWindow;
	ISampleGrabber* Grabber;
	IBaseFilter* GrabberFilter;
	ISampleGrabberCB* GrabberCallback;
	int StreamIndex;
	int FormatIndex;
}VideoDeviceContext;

typedef struct AudioInputDeviceContext{
	IGraphBuilder* Graph;
	ICaptureGraphBuilder2* Builder;
	IBaseFilter* CaptureFilter;
	IMediaControl* MediaControl;
	IVideoWindow* VideoWindow;
	ISampleGrabber* Grabber;
	IBaseFilter* GrabberFilter;
	ISampleGrabberCB* GrabberCallback;
	int StreamIndex;
	int FormatIndex;
}AudioInputDeviceContext;

typedef struct VideoOutputDeviceContext{
	/*ID2D1Factory* Factory;
	HWND Surface;
	RECT SurfaceSize;
	ID2D1HwndRenderTarget* Target;*/
}VideoOutputDeviceContext;

typedef struct AudioOutputDeviceContext{
	HWAVEOUT DeviceHandle;
	WAVEHDR * ActivePackets[100];
	bool Stopped;
	HANDLE Thread;
}AudioOutputDeviceContext;

void CALLBACK AudioOutProc(HWAVEOUT hwo, UINT uMsg, DWORD_PTR dwInstance, DWORD_PTR dwParam1, DWORD_PTR dwParam2){
	if(uMsg == WOM_DONE){
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)dwInstance;
		WAVEHDR* hdr = (WAVEHDR*)dwParam1;
		if(context != NULL)
		{
			for(int x = 0; x < 100; x++)
			{
				if(context->ActivePackets[x] == NULL)
				{
					context->ActivePackets[x] = hdr;
					break;
				}

			}
		}
	}
}

void CleanAudioHeaders(AudioOutputDeviceContext* context){
	for(int x = 0; x < 100; x++){
		WAVEHDR* hdr = context->ActivePackets[x];
		if(hdr != NULL)
		{
			if(0 == waveOutUnprepareHeader(context->DeviceHandle, hdr, sizeof(WAVEHDR))){
				free((void*) hdr->lpData);
				free((void*)hdr);
				context->ActivePackets[x] = NULL;
			}
		}
	} 
}

DWORD WINAPI AudioOutThread(LPVOID lpParameter){
	AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)lpParameter;
	if(context != NULL)
	{
		while(!context->Stopped)
		{
			CleanAudioHeaders(context);
			Sleep(10);
		}
	}
	return 0;
}

/********************************************
Global functions
********************************************/
short GetBPPEnum(GUID rep)
{
	short maxBPP = 0;
	try{
		if (rep == MEDIASUBTYPE_RGB1)
			maxBPP = 1;
		else if(rep == MEDIASUBTYPE_RGB4)
			maxBPP = 4;
		else if(rep == MEDIASUBTYPE_RGB8)
			maxBPP = 8;
		else if(rep == MEDIASUBTYPE_RGB555)
			maxBPP = 15;
		else if(rep == MEDIASUBTYPE_RGB565)
			maxBPP = 16;
		else if(rep == MEDIASUBTYPE_RGB24)
			maxBPP = 24;
		else if(rep == MEDIASUBTYPE_RGB32)
			maxBPP = 31;
		else if(rep == MEDIASUBTYPE_ARGB32)
			maxBPP = 32;
		else if(rep == MEDIASUBTYPE_AYUV)
			maxBPP = 65;
		else if(rep == MEDIASUBTYPE_UYVY)
			maxBPP = 66;
		else if(rep == MEDIASUBTYPE_Y411)
			maxBPP = 67;
		else if(rep == MEDIASUBTYPE_Y41P)
			maxBPP = 68;
		else if(rep == MEDIASUBTYPE_Y211)
			maxBPP = 69;
		else if(rep == MEDIASUBTYPE_YUY2)
			maxBPP = 70;
		else if(rep == MEDIASUBTYPE_YVYU)
			maxBPP = 71;
		else if(rep == MEDIASUBTYPE_YUYV)
			maxBPP = 72;
		else if(rep == MEDIASUBTYPE_IF09)
			maxBPP = 73;
		else if(rep == MEDIASUBTYPE_IYUV)
			maxBPP = 74;
		else if(rep == MEDIASUBTYPE_YV12)
			maxBPP = 75;
		else if(rep == MEDIASUBTYPE_YVU9)
			maxBPP = 76;
		else if(rep == WMMEDIASUBTYPE_I420)
			maxBPP = 77;
	}
	catch(...){}
	return maxBPP;
	
}

GUID GetBPPGUID(int rep)
{
	GUID maxBPP = MEDIASUBTYPE_RGB24;
	try{
		switch(rep)
		{
		case 1:
			maxBPP = MEDIASUBTYPE_RGB1;
			break;
		case 4:
			maxBPP = MEDIASUBTYPE_RGB4;
			break;
		case 8:
			maxBPP = MEDIASUBTYPE_RGB8;
			break;
		case 15:
			maxBPP = MEDIASUBTYPE_RGB555;
			break;
		case 16:
			maxBPP = MEDIASUBTYPE_RGB565;
			break;
		case 24:
			maxBPP = MEDIASUBTYPE_RGB24;
			break;
		case 31:
			maxBPP = MEDIASUBTYPE_RGB32;
			break;
		case 32:
			maxBPP = MEDIASUBTYPE_ARGB32;
			break;
		case 65:
			maxBPP = MEDIASUBTYPE_AYUV;
			break;
		case 66:
			maxBPP = MEDIASUBTYPE_UYVY;
			break;
		case 67:
			maxBPP = MEDIASUBTYPE_Y411;
			break;
		case 68:
			maxBPP = MEDIASUBTYPE_Y41P;
			break;
		case 69:
			maxBPP = MEDIASUBTYPE_Y211;
			break;
		case 70:
			maxBPP = MEDIASUBTYPE_YUY2;
			break;
		case 71:
			maxBPP = MEDIASUBTYPE_YVYU;
			break;
		case 72:
			maxBPP = MEDIASUBTYPE_YUYV;
			break;
		case 73:
			maxBPP = MEDIASUBTYPE_IF09;
			break;
		case 74:
			maxBPP = MEDIASUBTYPE_IYUV;
			break;
		case 75:
			maxBPP = MEDIASUBTYPE_YV12;
			break;
		case 76:
			maxBPP = MEDIASUBTYPE_YVU9;
			break;
		case 77:
			maxBPP = WMMEDIASUBTYPE_I420;
			break;
		}
	}
	catch(...){}
	return maxBPP;
}



HRESULT GetPin( IBaseFilter * pFilter, PIN_DIRECTION dirrequired, int iNum, IPin **ppPin)
{
    IEnumPins* pEnum;
    *ppPin = NULL;

    HRESULT hr; 
	
	try{
		hr = pFilter->EnumPins(&pEnum);
		if(FAILED(hr)) 
			return hr;

		ULONG ulFound;
		IPin *pPin;
		hr = E_FAIL;

		while(S_OK == pEnum->Next(1, &pPin, &ulFound))
		{
			PIN_DIRECTION pindir = (PIN_DIRECTION)3;

			pPin->QueryDirection(&pindir);
			if(pindir == dirrequired)
			{
				if(iNum == 0)
				{
					*ppPin = pPin;  // Return the pin's interface
					hr = S_OK;      // Found requested pin, so clear error
					break;
				}
				iNum--;
			} 

			pPin->Release();
		} 
	}
	catch(...){}

    return hr;
}


IPin * GetInPin( IBaseFilter * pFilter, int nPin )
{
    IPin* pComPin=0;
	try{
		GetPin(pFilter, PINDIR_INPUT, nPin, &pComPin);
	}
	catch(...){}
    return pComPin;
}


IPin * GetOutPin( IBaseFilter * pFilter, int nPin )
{
    IPin* pComPin=0;
	try{
		GetPin(pFilter, PINDIR_OUTPUT, nPin, &pComPin);
	}
	catch(...){}
    return pComPin;
}

void SetVideoMediaType(int mtIndex, VideoInputDeviceContext* context, double fps)
{
	HRESULT hr;
	try{
		IAMStreamConfig *pConfig = NULL;
		hr = context->Builder->FindInterface(
			&PIN_CATEGORY_CAPTURE, // Preview pin.
			0,    // Any media type.
			context->CaptureFilter, // Pointer to the capture filter.
			IID_IAMStreamConfig, (void**)&pConfig);

		int iCount = 0, iSize = 0;
		hr = pConfig->GetNumberOfCapabilities(&iCount, &iSize);

		// Check the size to make sure we pass in the correct structure.
		if (iSize == sizeof(VIDEO_STREAM_CONFIG_CAPS))
		{
			if(mtIndex >= iCount || mtIndex < 0)
			{
				pConfig->Release();
				return;
			}
			// Use the video capabilities structure.
			VIDEO_STREAM_CONFIG_CAPS scc;
			AM_MEDIA_TYPE *pmtConfig;
			
				
			hr = pConfig->GetStreamCaps(mtIndex, &pmtConfig, (BYTE*)&scc);
			if (SUCCEEDED(hr))
			{
				if ((pmtConfig->majortype == MEDIATYPE_Video) &&
						(pmtConfig->formattype == FORMAT_VideoInfo) &&
						(pmtConfig->cbFormat >= sizeof (VIDEOINFOHEADER)) &&
						(pmtConfig->pbFormat != NULL))
				{
					VIDEOINFOHEADER *pVih = (VIDEOINFOHEADER*)pmtConfig->pbFormat;
					pVih->AvgTimePerFrame = 10000000/fps;	
					hr = pConfig->SetFormat(pmtConfig);
				}
			}
		}
	}
	catch(...){}
}

void SetAudioMediaType(int mtIndex, AudioInputDeviceContext* context)
{
	HRESULT hr;
	try{
		IAMStreamConfig *pConfig = NULL;
		hr = context->Builder->FindInterface(
			&PIN_CATEGORY_CAPTURE, // Preview pin.
			0,    // Any media type.
			context->CaptureFilter, // Pointer to the capture filter.
			IID_IAMStreamConfig, (void**)&pConfig);

		int iCount = 0, iSize = 0;
		hr = pConfig->GetNumberOfCapabilities(&iCount, &iSize);

		// Check the size to make sure we pass in the correct structure.
		if (iSize == sizeof(AUDIO_STREAM_CONFIG_CAPS))
		{
			if(mtIndex >= iCount || mtIndex < 0)
			{
				pConfig->Release();
				return;
			}
			// Use the Audio capabilities structure.
			AUDIO_STREAM_CONFIG_CAPS scc;
			AM_MEDIA_TYPE *pmtConfig;
			
				
			hr = pConfig->GetStreamCaps(mtIndex, &pmtConfig, (BYTE*)&scc);
			if (SUCCEEDED(hr))
			{
				if ((pmtConfig->majortype == MEDIATYPE_Audio) &&
						(pmtConfig->formattype == FORMAT_WaveFormatEx) &&
						(pmtConfig->cbFormat >= sizeof (WAVEFORMATEX)) &&
						(pmtConfig->pbFormat != NULL))
				{
					WAVEFORMATEX *pVih = (WAVEFORMATEX*)pmtConfig->pbFormat;
						
					hr = pConfig->SetFormat(pmtConfig);
				}
			}
		}
	}
	catch(...){}
}

void SampleCaptured(void* context, void* sender, void* sample, long size, long long timestamp){
	if(context != NULL)
	{
		DeviceListener* listener = (DeviceListener*)context;
		listener->SampleCaptured(sender, sample, size, timestamp);
	}
}

/********************************************
VideoMediaFormat Implementation
********************************************/
VideoMediaFormat::VideoMediaFormat(){

}

VideoMediaFormat::~VideoMediaFormat(){

}

/********************************************
AudioMediaFormat Implementation
********************************************/
AudioMediaFormat::AudioMediaFormat(){

}

AudioMediaFormat::~AudioMediaFormat(){

}

/********************************************
VideoInputDevice Implementation
********************************************/
VideoInputDevice::VideoInputDevice(){
	this->DeviceName = "";
	this->DeviceIndex = 0;
	this->Listener = NULL;
	this->DeviceContext = NULL;
	FormatCount = 0;
	CoInitialize(NULL);
}

Device_Errors VideoInputDevice::Open(MediaFormat* format){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		Close();
		VideoInputDeviceContext* context = new VideoInputDeviceContext();
		context->Builder = NULL;
		context->CaptureFilter = NULL;
		context->FormatIndex = 0;
		context->Grabber = NULL;
		context->GrabberCallback = NULL;
		context->GrabberFilter = NULL;
		context->Graph = NULL;
		context->MediaControl = NULL;
		context->StreamIndex = 0;
		context->VideoWindow = NULL;

		HRESULT hr = 0;
		hr = CoCreateInstance(CLSID_CaptureGraphBuilder2, NULL, 
			CLSCTX_INPROC_SERVER, IID_ICaptureGraphBuilder2, (void**)&context->Builder );
		
		if (SUCCEEDED(hr))
		{
			// Create the Filter Graph Manager.
			hr = CoCreateInstance(CLSID_FilterGraph, 0, CLSCTX_INPROC_SERVER,
				IID_IGraphBuilder, (void**)&context->Graph);
			if (SUCCEEDED(hr))
			{
				// Initialize the Capture Graph Builder.
				hr = context->Builder->SetFiltergraph(context->Graph);
				if(SUCCEEDED(hr))
				{
					//create grabber filter.
					hr = CoCreateInstance(CLSID_SampleGrabber, NULL, CLSCTX_INPROC_SERVER,
						IID_IBaseFilter, (void**)&context->GrabberFilter);
					if(SUCCEEDED(hr))
					{
						//create grabber context
						hr = context->GrabberFilter->QueryInterface(IID_ISampleGrabber, (void**)&context->Grabber);
						if(SUCCEEDED(hr))
						{
							AM_MEDIA_TYPE mt;
							VideoMediaFormat* vformat = (VideoMediaFormat*) format;
							ZeroMemory(&mt, sizeof(AM_MEDIA_TYPE));
							mt.majortype = MEDIATYPE_Video;
							//if the caller has specified any pixel format, then we default the output format to RGB24, otherwise
							// set the output format to the specified pixel format.
							if(vformat->PixelFormat == VideoPixelFormat::ANY)
							{
								sprintf(dbg_buffer, "Grabber set to 24-bits\n");
								DbgOut(dbg_buffer);
								mt.subtype = GetBPPGUID(24);
							}
							else{
								sprintf(dbg_buffer, "Grabber set to %d pixel format\n", vformat->PixelFormat);
								DbgOut(dbg_buffer);
								mt.subtype = GetBPPGUID(vformat->PixelFormat);
							}
							
							ICreateDevEnum* pCreateDevEnum = 0;
							//enumerate and grab the specified device from the device index of this object.
							hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
							  IID_ICreateDevEnum, (void**)&pCreateDevEnum);
							if(SUCCEEDED(hr))
							{
								IEnumMoniker *pEm=0;
								hr = pCreateDevEnum->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &pEm, 0);
								if(SUCCEEDED(hr))
								{
									hr = pEm->Reset();
									IMoniker *pM = NULL;
									ULONG cFetched = 0;
									sprintf(dbg_buffer, "Requested Device %d\n",DeviceIndex);
									DbgOut(dbg_buffer);
									for(int uIndex=0; uIndex <= DeviceIndex; uIndex++)
									{
										SAFERELEASE(pM);
										hr = pEm->Next(1, &pM, &cFetched);
									}
									context->StreamIndex = DeviceIndex;
									if(pM != NULL)
									{
										hr = pM->BindToObject((int)0, (int)0, IID_IBaseFilter, (void**)&context->CaptureFilter);
										SAFERELEASE(pM);
										//Find the index of the provided format in the formats list and set the Capture filter to use this format.
										if(SUCCEEDED(hr))
										{
											sprintf(dbg_buffer, "Requested format - Width:%d, Height: %d, Pixel: %d\n",  vformat->Width, vformat->Height, vformat->PixelFormat);
											DbgOut(dbg_buffer);
											for(int x = 0; x < Formats.size(); x++)
											{
												VideoMediaFormat* f = (VideoMediaFormat*)Formats[x];
												//if we have not specified a pixel format and we have found a media format that matched the width
												// and height specified, then set the capture filter to use that format, otherwise, find the specific
												// video format with the specified pixel format and set the filter to use it.
												/*if(vformat->PixelFormat == VideoPixelFormat::ANY)
												{*/
													if(vformat->Width == f->Width && vformat->Height == f->Height)
													{
														sprintf(dbg_buffer, "Picked format #%d. Width:%d, Height: %d, Pixel: %d\n", x, f->Width, f->Height, f->PixelFormat);
														DbgOut(dbg_buffer);
														vformat->PixelFormat = f->PixelFormat;
														SetVideoMediaType(x, context, vformat->FPS);
														context->FormatIndex = x;
														break;
													}
												/*}
												else{
													if(vformat->Width == f->Width && vformat->Height == f->Height && vformat->PixelFormat == f->PixelFormat)
													{
														SetVideoMediaType(x, context);
														context->FormatIndex = x;
														break;
													}
												}*/
											}
											//add the capture filter to the Directshow graph.
											hr = context->Graph->AddFilter(context->CaptureFilter, L"Capture Filter");
											if(SUCCEEDED(hr))
											{
												//add the grabber filter to the directshow graph.
												hr = context->Graph->AddFilter(context->GrabberFilter, L"Sample Grabber");
												if(SUCCEEDED(hr))
												{
													//set the media type for the grabber.
													hr = context->Grabber->SetMediaType(&mt);
													if(SUCCEEDED(hr))
													{
														IPin* inPin = NULL;
														IPin* outPin = NULL;
														//get the first input pin for the grabber filter.
														inPin = GetInPin(context->GrabberFilter, 0);
														if(inPin != NULL)
														{
															//get the first output pin for the capture filter.
															hr = context->Builder->FindPin(context->CaptureFilter,PINDIR_OUTPUT,&PIN_CATEGORY_CAPTURE, &MEDIATYPE_Video, FALSE, 0, &outPin); 
															if(SUCCEEDED(hr))
															{
																//use the graph to connect the input pin to the output pin.
																hr = context->Graph->Connect(outPin, inPin);
																if(SUCCEEDED(hr))
																{
																	//set the grabber properties.
																	context->Grabber->SetBufferSamples(FALSE);
																	context->Grabber->SetOneShot(FALSE);
																	//if a listener has been provided, we need to create a grabber callback.
																	if(Listener != NULL)
																	{
																		//get the pointer to the global capturing function.
																		void* func = &SampleCaptured;
																		//create a new callback based on the function, our listener, and this object.
																		context->GrabberCallback = new GrabberCB(func, Listener, this);
																		context->Grabber->SetCallback((ISampleGrabberCB*)context->GrabberCallback, 1);
																		//turn off autopreview.
																		hr = context->Graph->QueryInterface(IID_IVideoWindow,(void**) &context->VideoWindow);
																		if(SUCCEEDED(hr))
																			context->VideoWindow->put_AutoShow(OAFALSE);
																		//start the capturing on the graph.
																		hr = context->Graph->QueryInterface(IID_IMediaControl,(void**) &context->MediaControl);
																		if(SUCCEEDED(hr))
																		{
																			hr = context->MediaControl->Run();
																			if(SUCCEEDED(hr)){
																				//if all is successful, we return "SUCCEEDED and we will set the
																				//DeviceContext member variable to be the context we have created.
																				//This context will be used in all intermediate functions from now
																				// on to handle the processes involved with receiving the inputs and
																				// with deallocating everything at the end.
																				DeviceContext = context;
																			}
																			else{
																				retval = Device_Errors::NO_INPUT;
																			}
																		}
																		else{
																			retval = Device_Errors::NO_INPUT;
																		}
																	}
																}
																else{
																	retval = Device_Errors::INVALID_FORMAT;
																}
															}
															else{
																retval = Device_Errors::INVALID_FORMAT;
															}
														}
														else{
															retval = Device_Errors::INVALID_FORMAT;
														}
														
													}
													else{
														retval = Device_Errors::INVALID_FORMAT;
													}
												}
												else{
													retval = Device_Errors::INVALID_DEVICE;
												}
											}
											else{
												retval = Device_Errors::INVALID_DEVICE;
											}
										}
										else{
											retval = Device_Errors::INVALID_DEVICE;
										}
									}
									else{
										retval = Device_Errors::INVALID_DEVICE;
									}
									SAFERELEASE(pEm);
								}
								SAFERELEASE(pCreateDevEnum);
							}
							else{
								retval = Device_Errors::NO_DEVICES;
							}
						}
						else{
							retval = Device_Errors::NO_DEVICES;
						}
					}
					else{
						retval = Device_Errors::NO_DEVICES;
					}
					

				}
				else{
					retval = Device_Errors::NO_DEVICES;
				}
			}
			else
			{
				retval = Device_Errors::NO_DEVICES;
			}
		}
		else{
			retval = Device_Errors::NO_DEVICES;
		}

		if(retval != Device_Errors::SUCCEEDED)
		{
			SAFERELEASE(context->VideoWindow);
			SAFERELEASE(context->GrabberCallback);
			SAFERELEASE(context->MediaControl);
			SAFERELEASE(context->CaptureFilter);
			SAFERELEASE(context->Grabber);
			SAFERELEASE(context->GrabberFilter);
			SAFERELEASE(context->Graph);
			SAFERELEASE(context->Builder);
		}
	}
	catch(...)
	{
		Device_Errors retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

Device_Errors VideoInputDevice::Close(){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		if(DeviceContext != NULL)
		{
			VideoInputDeviceContext* context = (VideoInputDeviceContext*)DeviceContext;
			if(context->MediaControl != NULL)
				context->MediaControl->Stop();
			SAFERELEASE(context->VideoWindow);
			SAFERELEASE(context->GrabberCallback);
			SAFERELEASE(context->MediaControl);
			SAFERELEASE(context->CaptureFilter);
			SAFERELEASE(context->Grabber);
			SAFERELEASE(context->GrabberFilter);
			SAFERELEASE(context->Graph);
			SAFERELEASE(context->Builder);
		}
		SAFEDELETE(DeviceContext);
	}
	catch(...){
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

Device_Errors VideoInputDevice::GetDevices(vector<Device*> &deviceList){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	//CoInitialize(NULL);
	try
	{
		SHORT    uIndex = 0;
    
		HRESULT hr;
		BOOL bCheck = FALSE;
		VARIANT var;
		var.vt = VT_BSTR;

		ICreateDevEnum *pCreateDevEnum=0;
		hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
							  IID_ICreateDevEnum, (void**)&pCreateDevEnum);

		if(hr != NOERROR)
		{
			retval = Device_Errors::NO_DEVICES;
		}
		else{
			IEnumMoniker *pEm=0;
			hr = pCreateDevEnum->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, &pEm, 0);
			if(hr != NOERROR)
			{
				retval = Device_Errors::NO_DEVICES;
			}
			else{
				pEm->Reset();
				ULONG cFetched;
				IMoniker *pM;
				IGraphBuilder* pGraph = NULL; //Main filter graph
				ICaptureGraphBuilder2* pBuild = NULL; //main graph builder
				hr = CoCreateInstance(CLSID_CaptureGraphBuilder2, NULL, 
						CLSCTX_INPROC_SERVER, IID_ICaptureGraphBuilder2, (void**)&pBuild );
				if(hr != NOERROR)
				{
					retval = Device_Errors::NO_DEVICES;
				}
				else
				{
					hr = CoCreateInstance(CLSID_FilterGraph, 0, CLSCTX_INPROC_SERVER,
						IID_IGraphBuilder, (void**)&pGraph);
					if(hr != NOERROR)
					{
						retval = Device_Errors::NO_DEVICES;
					}
					else{
						hr = pBuild->SetFiltergraph(pGraph);
						for(uIndex=0;; uIndex++)
						{
							IPropertyBag *pBag=0;
							hr = pEm->Next(1, &pM, &cFetched);
							if(hr != S_OK) break;
							hr = pM->BindToStorage(0, 0, IID_IPropertyBag, (void **)&pBag);
							if(SUCCEEDED(hr))
							{
	            
								hr = pBag->Read(L"FriendlyName", &var, NULL);
								pBag->Release();
								VideoInputDevice* vid = new VideoInputDevice();
								vid->DeviceIndex = uIndex;
								string name(ConvertBSTRToString(var.bstrVal));
								vid->DeviceName = name;
								vid->FormatCount = 0;
								IBaseFilter *pCap = NULL;
								hr = pM->BindToObject((int)0, (int)0, IID_IBaseFilter, (void**)&pCap);
								if(SUCCEEDED(hr))
								{
									IAMStreamConfig *pConfig = NULL;
									hr = pBuild->FindInterface(
										&PIN_CATEGORY_CAPTURE, // Preview pin.
										0,    // Any media type.
										pCap, // Pointer to the capture filter.
										IID_IAMStreamConfig, (void**)&pConfig);
									if(SUCCEEDED(hr))
									{
										int iCount = 0, iSize = 0;
										hr = pConfig->GetNumberOfCapabilities(&iCount, &iSize);

										// Check the size to make sure we pass in the correct structure.
										if (iSize == sizeof(VIDEO_STREAM_CONFIG_CAPS))
										{
											// Use the video capabilities structure.
											LONG maxWidth = 0;
											LONG maxHeight = 0;
											DOUBLE maxFPS = 0;
											short maxBPP = 0;
											for (int iFormat = 0; iFormat < iCount; iFormat++)
											{
												VIDEO_STREAM_CONFIG_CAPS scc;
												AM_MEDIA_TYPE *pmtConfig;
												hr = pConfig->GetStreamCaps(iFormat, &pmtConfig, (BYTE*)&scc);
												if (SUCCEEDED(hr))
												{
													if ((pmtConfig->majortype == MEDIATYPE_Video) &&
														(pmtConfig->formattype == FORMAT_VideoInfo) &&
														(pmtConfig->cbFormat >= sizeof (VIDEOINFOHEADER)) &&
														(pmtConfig->pbFormat != NULL))
													{
														VIDEOINFOHEADER *pVih = (VIDEOINFOHEADER*)pmtConfig->pbFormat;
						
														maxWidth = pVih->bmiHeader.biWidth;
														maxHeight = pVih->bmiHeader.biHeight;
														maxFPS = 10000000/pVih->AvgTimePerFrame;
							
														maxBPP = GetBPPEnum(pmtConfig->subtype);
														VideoMediaFormat* format = new VideoMediaFormat();
														format->PixelFormat = (VideoPixelFormat)maxBPP;
														format->Width = maxWidth;
														format->Height = maxHeight;
														format->VideoType = 0;
														format->FPS = maxFPS;
														vid->Formats.push_back(format);
														vid->FormatCount++;
													}
												}
											}
										}
										pConfig->Release();
									}
									
								}
								SAFERELEASE(pCap);
								deviceList.push_back(vid);
							}

							pM->Release();
						}
						pEm->Release();
					}
					
				}
				SAFERELEASE(pGraph);
				SAFERELEASE(pBuild);
			}
		}

	}
	catch(...)
	{
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

VideoInputDevice::~VideoInputDevice(){
	Close();
	for(int x=0; x < FormatCount; x++)
	{
		if(Formats[x] != NULL)
		{
				delete(Formats[x]);
				Formats[x] = NULL;
		}
	}
	Formats.clear();
}

/********************************************
AudioInputDevice Implementation
*********************************************/

AudioInputDevice::AudioInputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CoInitialize(NULL);
}

Device_Errors AudioInputDevice::Open(MediaFormat* format){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		Close();
		AudioInputDeviceContext* context = new AudioInputDeviceContext();
		context->Builder = NULL;
		context->CaptureFilter = NULL;
		context->FormatIndex = 0;
		context->Grabber = NULL;
		context->GrabberCallback = NULL;
		context->GrabberFilter = NULL;
		context->Graph = NULL;
		context->MediaControl = NULL;
		context->StreamIndex = 0;
		
		HRESULT hr = 0;
		hr = CoCreateInstance(CLSID_CaptureGraphBuilder2, NULL, 
			CLSCTX_INPROC_SERVER, IID_ICaptureGraphBuilder2, (void**)&context->Builder );
		
		if (SUCCEEDED(hr))
		{
			// Create the Filter Graph Manager.
			hr = CoCreateInstance(CLSID_FilterGraph, 0, CLSCTX_INPROC_SERVER,
				IID_IGraphBuilder, (void**)&context->Graph);
			if (SUCCEEDED(hr))
			{
				// Initialize the Capture Graph Builder.
				hr = context->Builder->SetFiltergraph(context->Graph);
				if(SUCCEEDED(hr))
				{
					//create grabber filter.
					hr = CoCreateInstance(CLSID_SampleGrabber, NULL, CLSCTX_INPROC_SERVER,
						IID_IBaseFilter, (void**)&context->GrabberFilter);
					if(SUCCEEDED(hr))
					{
						//create grabber context
						hr = context->GrabberFilter->QueryInterface(IID_ISampleGrabber, (void**)&context->Grabber);
						if(SUCCEEDED(hr))
						{
							AM_MEDIA_TYPE mt;
							AudioMediaFormat* vformat = (AudioMediaFormat*) format;
							ZeroMemory(&mt, sizeof(AM_MEDIA_TYPE));
							mt.majortype = MEDIATYPE_Audio;
							mt.subtype = MEDIASUBTYPE_PCM;
							
							ICreateDevEnum* pCreateDevEnum = 0;
							//enumerate and grab the specified device from the device index of this object.
							hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
							  IID_ICreateDevEnum, (void**)&pCreateDevEnum);
							if(SUCCEEDED(hr))
							{
								IEnumMoniker *pEm=0;
								hr = pCreateDevEnum->CreateClassEnumerator(CLSID_AudioInputDeviceCategory, &pEm, 0);
								if(SUCCEEDED(hr))
								{
									hr = pEm->Reset();
									IMoniker *pM = NULL;
									ULONG cFetched = 0;
									for(int uIndex=0; uIndex <= DeviceIndex; uIndex++)
									{
										SAFERELEASE(pM);
										hr = pEm->Next(1, &pM, &cFetched);
									}
									context->StreamIndex = DeviceIndex;
									if(pM != NULL)
									{
										hr = pM->BindToObject((int)0, (int)0, IID_IBaseFilter, (void**)&context->CaptureFilter);
										SAFERELEASE(pM);
										//Find the index of the provided format in the formats list and set the Capture filter to use this format.
										if(SUCCEEDED(hr))
										{
											for(int x = 0; x < Formats.size(); x++)
											{
												AudioMediaFormat* f = (AudioMediaFormat*)Formats[x];
												//if we have not specified a pixel format and we have found a media format that matched the width
												// and height specified, then set the capture filter to use that format, otherwise, find the specific
												// Audio format with the specified pixel format and set the filter to use it.
												if(vformat->SampleRate == f->SampleRate && vformat->BitsPerSample == f->BitsPerSample && vformat->Channels == f->Channels)
												{
													SetAudioMediaType(x, context);
													context->FormatIndex = x;
													break;
												}
											}
											//add the capture filter to the Directshow graph.
											hr = context->Graph->AddFilter(context->CaptureFilter, L"Capture Filter");
											if(SUCCEEDED(hr))
											{
												//add the grabber filter to the directshow graph.
												hr = context->Graph->AddFilter(context->GrabberFilter, L"Sample Grabber");
												if(SUCCEEDED(hr))
												{
													IAMBufferNegotiation* pBN;
													hr = context->Builder->FindInterface(NULL, NULL, context->CaptureFilter, IID_IAMBufferNegotiation, (void**)&pBN);
													//WriteErrorMsg("StartAudio.log", "Got buffer negotiation with return 0x%x\n", hr, true);
		
													ALLOCATOR_PROPERTIES ap;
													ap.cbBuffer = (vformat->BitsPerSample/8) * 240;
													ap.cBuffers = -1;
													ap.cbAlign = -1;
													ap.cbPrefix = -1;
													hr = pBN->SuggestAllocatorProperties(&ap);
													//WriteErrorMsg("StartAudio.log", "Set buffer size with return 0x%x\n", hr, true);
													pBN->Release();
													//set the media type for the grabber.
													hr = context->Grabber->SetMediaType(&mt);
													if(SUCCEEDED(hr))
													{
														IPin* inPin = NULL;
														IPin* outPin = NULL;
														//get the first input pin for the grabber filter.
														inPin = GetInPin(context->GrabberFilter, 0);
														if(inPin != NULL)
														{
															//get the first output pin for the capture filter.
															hr = context->Builder->FindPin(context->CaptureFilter,PINDIR_OUTPUT,&PIN_CATEGORY_CAPTURE, &MEDIATYPE_Audio, FALSE, 0, &outPin); 
															if(SUCCEEDED(hr))
															{
																//use the graph to connect the input pin to the output pin.
																hr = context->Graph->Connect(outPin, inPin);
																if(SUCCEEDED(hr))
																{
																	//set the grabber properties.
																	context->Grabber->SetBufferSamples(FALSE);
																	context->Grabber->SetOneShot(FALSE);
																	//if a listener has been provided, we need to create a grabber callback.
																	if(Listener != NULL)
																	{
																		//get the pointer to the global capturing function.
																		void* func = &SampleCaptured;
																		//create a new callback based on the function, our listener, and this object.
																		context->GrabberCallback = new GrabberCB(func, Listener, this);
																		context->Grabber->SetCallback((ISampleGrabberCB*)context->GrabberCallback, 1);
																		//turn off autopreview.
																		hr = context->Graph->QueryInterface(IID_IMediaControl,(void**) &context->MediaControl);
																		if(SUCCEEDED(hr))
																		{
																			hr = context->MediaControl->Run();
																			if(SUCCEEDED(hr)){
																				//if all is successful, we return "SUCCEEDED and we will set the
																				//DeviceContext member variable to be the context we have created.
																				//This context will be used in all intermediate functions from now
																				// on to handle the processes involved with receiving the inputs and
																				// with deallocating everything at the end.
																				DeviceContext = context;
																			}
																			else{
																				retval = Device_Errors::NO_INPUT;
																			}
																		}
																		else{
																			retval = Device_Errors::NO_INPUT;
																		}
																	}
																}
																else{
																	retval = Device_Errors::INVALID_FORMAT;
																}
															}
															else{
																retval = Device_Errors::INVALID_FORMAT;
															}
														}
														else{
															retval = Device_Errors::INVALID_FORMAT;
														}
														
													}
													else{
														retval = Device_Errors::INVALID_FORMAT;
													}
												}
												else{
													retval = Device_Errors::INVALID_DEVICE;
												}
											}
											else{
												retval = Device_Errors::INVALID_DEVICE;
											}
										}
										else{
											retval = Device_Errors::INVALID_DEVICE;
										}
									}
									else{
										retval = Device_Errors::INVALID_DEVICE;
									}
									SAFERELEASE(pEm);
								}
								SAFERELEASE(pCreateDevEnum);
							}
							else{
								retval = Device_Errors::NO_DEVICES;
							}
						}
						else{
							retval = Device_Errors::NO_DEVICES;
						}
					}
					else{
						retval = Device_Errors::NO_DEVICES;
					}
					

				}
				else{
					retval = Device_Errors::NO_DEVICES;
				}
			}
			else
			{
				retval = Device_Errors::NO_DEVICES;
			}
		}
		else{
			retval = Device_Errors::NO_DEVICES;
		}

		if(retval != Device_Errors::SUCCEEDED)
		{
			SAFERELEASE(context->GrabberCallback);
			SAFERELEASE(context->MediaControl);
			SAFERELEASE(context->CaptureFilter);
			SAFERELEASE(context->Grabber);
			SAFERELEASE(context->GrabberFilter);
			SAFERELEASE(context->Graph);
			SAFERELEASE(context->Builder);
		}
	}
	catch(...)
	{
		Device_Errors retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

Device_Errors AudioInputDevice::Close(){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		if(DeviceContext != NULL)
		{
			AudioInputDeviceContext* context = (AudioInputDeviceContext*)DeviceContext;
			if(context->MediaControl != NULL)
				context->MediaControl->Stop();
			SAFERELEASE(context->GrabberCallback);
			SAFERELEASE(context->MediaControl);
			SAFERELEASE(context->CaptureFilter);
			SAFERELEASE(context->Grabber);
			SAFERELEASE(context->GrabberFilter);
			SAFERELEASE(context->Graph);
			SAFERELEASE(context->Builder);
			
		}
		SAFEDELETE(DeviceContext);
	}
	catch(...){
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

Device_Errors AudioInputDevice::GetDevices(vector<Device*> &deviceList){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		SHORT    uIndex = 0;
    
		HRESULT hr;
		BOOL bCheck = FALSE;
		VARIANT var;
		var.vt = VT_BSTR;

		ICreateDevEnum *pCreateDevEnum=0;
		hr = CoCreateInstance(CLSID_SystemDeviceEnum, NULL, CLSCTX_INPROC_SERVER,
							  IID_ICreateDevEnum, (void**)&pCreateDevEnum);

		if(hr != NOERROR)
		{
			retval = Device_Errors::NO_DEVICES;
		}
		else{
			IEnumMoniker *pEm=0;
			hr = pCreateDevEnum->CreateClassEnumerator(CLSID_AudioInputDeviceCategory, &pEm, 0);
			if(hr != NOERROR)
			{
				retval = Device_Errors::NO_DEVICES;
			}
			else{
				pEm->Reset();
				ULONG cFetched;
				IMoniker *pM;
				IGraphBuilder* pGraph = NULL; //Main filter graph
				ICaptureGraphBuilder2* pBuild = NULL; //main graph builder
				hr = CoCreateInstance(CLSID_CaptureGraphBuilder2, NULL, 
						CLSCTX_INPROC_SERVER, IID_ICaptureGraphBuilder2, (void**)&pBuild );
				if(hr != NOERROR)
				{
					retval = Device_Errors::NO_DEVICES;
				}
				else
				{
					hr = CoCreateInstance(CLSID_FilterGraph, 0, CLSCTX_INPROC_SERVER,
						IID_IGraphBuilder, (void**)&pGraph);
					if(hr != NOERROR)
					{
						retval = Device_Errors::NO_DEVICES;
					}
					else{
						hr = pBuild->SetFiltergraph(pGraph);
						for(uIndex=0;; uIndex++)
						{
							IPropertyBag *pBag=0;
							hr = pEm->Next(1, &pM, &cFetched);
							if(hr != S_OK) break;
							hr = pM->BindToStorage(0, 0, IID_IPropertyBag, (void **)&pBag);
							if(SUCCEEDED(hr))
							{
	            
								hr = pBag->Read(L"FriendlyName", &var, NULL);
								pBag->Release();
								AudioInputDevice* vid = new AudioInputDevice();
								vid->DeviceIndex = uIndex;
								string name(ConvertBSTRToString(var.bstrVal));
								vid->DeviceName = name;
								vid->FormatCount = 0;
								IBaseFilter *pCap = NULL;
								hr = pM->BindToObject((int)0, (int)0, IID_IBaseFilter, (void**)&pCap);
								if(SUCCEEDED(hr))
								{
									IAMStreamConfig *pConfig = NULL;
									hr = pBuild->FindInterface(
										&PIN_CATEGORY_CAPTURE, // Preview pin.
										0,    // Any media type.
										pCap, // Pointer to the capture filter.
										IID_IAMStreamConfig, (void**)&pConfig);
									if(SUCCEEDED(hr))
									{
										int iCount = 0, iSize = 0;
										hr = pConfig->GetNumberOfCapabilities(&iCount, &iSize);

										// Check the size to make sure we pass in the correct structure.
										if (iSize == sizeof(AUDIO_STREAM_CONFIG_CAPS))
										{
											for (int iFormat = 0; iFormat < iCount; iFormat++)
											{
												AUDIO_STREAM_CONFIG_CAPS scc;
												AM_MEDIA_TYPE *pmtConfig;
												hr = pConfig->GetStreamCaps(iFormat, &pmtConfig, (BYTE*)&scc);
												if (SUCCEEDED(hr))
												{
													if ((pmtConfig->majortype == MEDIATYPE_Audio) &&
														(pmtConfig->formattype == FORMAT_WaveFormatEx) &&
														(pmtConfig->cbFormat >= sizeof (WAVEFORMATEX)) &&
														(pmtConfig->pbFormat != NULL))
													{
														WAVEFORMATEX *pVih = (WAVEFORMATEX*)pmtConfig->pbFormat;
						
														AudioMediaFormat* format = new AudioMediaFormat();
														format->BitsPerSample = pVih->wBitsPerSample;
														format->Channels = pVih->nChannels;
														format->SampleRate = pVih->nSamplesPerSec;
														vid->Formats.push_back(format);
														vid->FormatCount++;
													}
												}
											}
										}
										pConfig->Release();
									}
									
								}
								SAFERELEASE(pCap);
								deviceList.push_back(vid);
							}

							pM->Release();
						}
						pEm->Release();
					}
					
				}
				SAFERELEASE(pGraph);
				SAFERELEASE(pBuild);
			}
		}

	}
	catch(...)
	{
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

AudioInputDevice::~AudioInputDevice()
{
	Close();
	for(int x=0; x < FormatCount; x++)
	{
		if(Formats[x] != NULL)
		{
				delete(Formats[x]);
				Formats[x] = NULL;
		}
	}
	Formats.clear();
};

/********************************************
VideoOutputDevice Implementation
********************************************/
VideoOutputDevice::VideoOutputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
	CoInitialize(NULL);
}
	//See OutputDevice header.
Device_Errors VideoOutputDevice::Present(void* sample, long size, long long timestamp){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}
	//See Device Header.
Device_Errors VideoOutputDevice::Open(MediaFormat* format){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}
	//Opens the output device with a specified surface, width, height and rotation.
Device_Errors VideoOutputDevice::Open(MediaFormat* format, void* surface, int width, int height, bool rotate){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		Surface = surface;
		SurfaceWidth = width;
		SurfaceHeight = height;
		RotateFrames = rotate;
		Open(format);
	}
	catch(...){
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

	//See Device Header
Device_Errors VideoOutputDevice::Close(){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try
	{
		
	}
	catch(...){
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}
	//See Device Header
Device_Errors VideoOutputDevice::GetDevices(vector<Device*> &deviceList){
	return Device_Errors::NOT_SUPPORTED;
}

VideoOutputDevice::~VideoOutputDevice(){
	Close();
}

/*********************************************
AudioOutputDevice Implementation
*********************************************/
AudioOutputDevice::AudioOutputDevice(){
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
	CoInitialize(NULL);
}
	//See OutputDevice header.
Device_Errors AudioOutputDevice::Present(void* sample, long size, long long timestamp){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)DeviceContext;
		if(DeviceContext == NULL){
			retval = Device_Errors::INVALID_DEVICE;
		}
		else if(context->DeviceHandle == NULL){
			retval = Device_Errors::INVALID_DEVICE;
		}
		else if(sample != NULL)
		{
			WAVEHDR* hdr = (WAVEHDR*)malloc(sizeof(WAVEHDR));
			hdr->dwBufferLength = size;
			hdr->dwBytesRecorded = size;
			hdr->dwFlags = 0;
			hdr->dwLoops = 0;
			hdr->dwUser = 0;
			hdr->lpData = (char*)malloc(size);
			memcpy(hdr->lpData, (void*)sample, size);
			if(waveOutPrepareHeader(context->DeviceHandle,hdr,sizeof(WAVEHDR)) == 0){
				if(waveOutWrite(context->DeviceHandle, hdr, sizeof(WAVEHDR)) != 0)
				{
					retval = Device_Errors::INVALID_DATA;
					waveOutUnprepareHeader(context->DeviceHandle, hdr, sizeof(WAVEHDR));
					free(hdr->lpData);
					free(hdr);
				}
				
			}
			else{
				retval = Device_Errors::INVALID_DATA;
				free(hdr->lpData);
				free(hdr);
			}
		}
		else{
			retval = Device_Errors::INVALID_DATA;
		}
	}
	catch(...)
	{
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::Open(MediaFormat* format){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = new AudioOutputDeviceContext();
		AudioMediaFormat* aformat = (AudioMediaFormat*)format;
		WAVEFORMATEX fmt;
		fmt.wFormatTag = WAVE_FORMAT_PCM;
		fmt.nChannels = aformat->Channels;
		fmt.nSamplesPerSec = aformat->SampleRate;
		fmt.wBitsPerSample = aformat->BitsPerSample;
		fmt.nAvgBytesPerSec = (aformat->SampleRate * aformat->BitsPerSample)/8;
		fmt.nBlockAlign = (aformat->Channels * aformat->BitsPerSample)/8;
		fmt.cbSize = 0;
		MMRESULT r = waveOutOpen(&context->DeviceHandle, DeviceIndex, &fmt, (DWORD_PTR)&AudioOutProc, (DWORD_PTR)context, CALLBACK_FUNCTION);
		if(r == MMSYSERR_NOERROR)
		{
			DeviceContext = context;
			context->Stopped = false;
			for(int x = 0; x < 100; x++)
				context->ActivePackets[x] = NULL;
			context->Thread = CreateThread(NULL,0,&AudioOutThread, context, 0, NULL);
		}
		else{
			delete(context);
			retval = Device_Errors::INVALID_DEVICE;
		}
	}
	catch(...)
	{
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::Close(){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try{
		AudioOutputDeviceContext* context = (AudioOutputDeviceContext*)DeviceContext;
		if(context != NULL){
			waveOutClose(context->DeviceHandle);
			Sleep(20);
			context->Stopped = true;
			CleanAudioHeaders(context);
			
		}
		SAFEDELETE(DeviceContext);
	}
	catch(...)
	{
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}
	//See Device header.
Device_Errors AudioOutputDevice::GetDevices(vector<Device*> &deviceList){
	Device_Errors retval = Device_Errors::SUCCEEDED;
	try{
		WAVEOUTCAPS* woc = NULL;
		int devCount = waveOutGetNumDevs();
		if(devCount > 0)
		{
			for(int x = 0; x < devCount; x++)
			{
				woc = (WAVEOUTCAPS*) malloc(sizeof(WAVEOUTCAPS));
				if(SUCCEEDED(waveOutGetDevCaps(x, woc, sizeof(WAVEOUTCAPS))))
				{
					
					char* cname = new char[wcslen(woc->szPname)];
					sprintf(cname, "%S", woc->szPname);
					string name(cname);
					//delete [] cname;
					AudioOutputDevice* ao = new AudioOutputDevice();
					ao->DeviceIndex = x;
					ao->DeviceName = name;
					deviceList.push_back(ao);
				}
				free(woc);
			}
		}
	}
	catch(...)
	{
		retval = Device_Errors::UNEXPECTED;
	}
	return retval;
}

AudioOutputDevice::~AudioOutputDevice(){
	Close();
	DeviceName = "";
	DeviceIndex = 0;
	Listener = NULL;
	DeviceContext = NULL;
	FormatCount = 0;
	CurrentFormat = NULL;
}
