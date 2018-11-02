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
#include <new>
#include <dmo.h>
class CMediaBuffer : public IMediaBuffer
{
private:
    DWORD        m_cbLength;
    const DWORD  m_cbMaxLength;
    LONG         m_cRef;
    BYTE         *m_pbData;
	bool		 outsideSet;

public:
    CMediaBuffer(DWORD cbMaxLength) :
        m_cRef(0),
        m_cbMaxLength(cbMaxLength),
        m_cbLength(0),
        m_pbData(NULL)
    {
        m_pbData = new BYTE[cbMaxLength];
		outsideSet = false;
        if (!m_pbData) throw std::bad_alloc();
    }

    ~CMediaBuffer()
    {
        if (m_pbData && !outsideSet) {
            delete [] m_pbData;
        }
    }

    // Function to create a new IMediaBuffer object and return 
    // an AddRef'd interface pointer.
    static HRESULT CreateBuffer(long cbMaxLen, REFIID iid, void **ppUnk)
    {
        try {
            CMediaBuffer *pBuffer = new CMediaBuffer(cbMaxLen);
            return pBuffer->QueryInterface(iid, ppUnk);
        }
        catch (std::bad_alloc)
        {
            return E_OUTOFMEMORY;
        }
    }

    // IUnknown methods.
    STDMETHODIMP QueryInterface(REFIID riid, void **ppv)
    {
        if (ppv == NULL) {
            return E_POINTER;
        }
        if (riid == IID_IMediaBuffer || riid == IID_IUnknown) {
            *ppv = static_cast<IMediaBuffer *>(this);
            AddRef();
            return S_OK;
        }
        *ppv = NULL;
        return E_NOINTERFACE;
    }

    STDMETHODIMP_(ULONG) AddRef()
    {
        return InterlockedIncrement(&m_cRef);
    }

    STDMETHODIMP_(ULONG) Release()
    {
        LONG lRef = InterlockedDecrement(&m_cRef);
        if (lRef == 0) {
            delete this;
            // m_cRef is no longer valid! Return lRef.
        }
        return lRef;  
    }

    // IMediaBuffer methods.
    STDMETHODIMP SetLength(DWORD cbLength)
    {
        if (cbLength > m_cbMaxLength) {
            return E_INVALIDARG;
        } else {
            m_cbLength = cbLength;
            return S_OK;
        }
    }

    STDMETHODIMP GetMaxLength(DWORD *pcbMaxLength)
    {
        if (pcbMaxLength == NULL) {
            return E_POINTER;
        }
        *pcbMaxLength = m_cbMaxLength;
        return S_OK;
    }

	STDMETHODIMP SetBufferAndLength(BYTE* pBuffer, DWORD length)
	{
		if (pBuffer == NULL || length == 0) {
            return E_POINTER;
        }
		if(m_pbData != NULL)
			delete [] m_pbData;
		outsideSet = true;
        m_pbData = pBuffer;
        m_cbLength = length;
        return S_OK;
	}

    STDMETHODIMP GetBufferAndLength(BYTE **ppbBuffer, DWORD *pcbLength)
    {
        if (ppbBuffer == NULL || pcbLength == NULL) {
            return E_POINTER;
        }
        *ppbBuffer = m_pbData;
        *pcbLength = m_cbLength;
        return S_OK;
    }
};

