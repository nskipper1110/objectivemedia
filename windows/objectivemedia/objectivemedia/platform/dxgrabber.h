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
//////////////////////////////////////////////////////////////////////////////////////
// Grabber Callback definition


class GrabberCB : public ISampleGrabberCB
{
public:
	GrabberCB(void* ownFunc, void* cont, void* sender);
	STDMETHODIMP_(ULONG) AddRef() { return 2; }
    STDMETHODIMP_(ULONG) Release() { return 1; }

    // Fake out any COM QI'ing
    //
    STDMETHODIMP QueryInterface(REFIID riid, void ** ppv)
    {
		try{
			if( riid == IID_ISampleGrabberCB || riid == IID_IUnknown ) 
			{
				*ppv = (void *) static_cast<ISampleGrabberCB*> ( this );
				return NOERROR;
			}   
		}
		catch(...){}

        return E_NOINTERFACE;
    }

	
	STDMETHODIMP SampleCB( double SampleTime, IMediaSample * pSample );
    STDMETHODIMP BufferCB( double SampleTime, BYTE * pBuffer, long BufferSize );

private:
	void* Sender;
	void (*Owner)(void* context, void* sender, void* buffer, long bufSize, LONGLONG timestamp);
	void* context;
};

GrabberCB::GrabberCB(void* ownFunc, void* cont, void* sender){
	try{
		Owner = (void (*)(void*, void*, void*, long, LONGLONG))ownFunc;
		context = cont;
		Sender = sender;
	
	}
	catch(...){}
};

STDMETHODIMP GrabberCB::SampleCB( double SampleTime, IMediaSample * pSample )
{
    return 0;
}

STDMETHODIMP GrabberCB::BufferCB( double SampleTime, BYTE * pBuffer, long BufferSize )
{
	try{
		//if(VideoStopping == true) return 0;
		//VideoGrabbing = true;
		try
		{
			if(pBuffer == NULL || BufferSize <= 0) return 0;
			LONGLONG sTime = SampleTime * (10000000);
			
			
			//BYTE* buffer = (BYTE*)malloc(BufferSize);
			//memcpy((void*)buffer, (void*)pBuffer, BufferSize);
			Owner(context, Sender, pBuffer, BufferSize, sTime);
			//::CoTaskMemFree(pBuffer);
		}
		catch(...){}
		
		//VideoGrabbing = false;
	}
	catch(...){}
	
	return 0;
}