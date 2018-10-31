../emsdk-portable/emsdk install latest
../emsdk-portable/emsdk activate latest
source ../emsdk-portable/emsdk_env.sh
emconfigure ./configure --prefix=./build/js/x86 \
    --target-os=none arch=x86 \
    --enable-cross-compile \
    --cc="emcc" \
	--extra-cflags="-s ERROR_ON_UNDEFINED_SYMBOLS=0" \
    --disable-runtime-cpudetect \
    --disable-doc \
	--disable-asm \
    --enable-gpl \
	--disable-fast-unaligned \
	--disable-pthreads \
	--disable-w32threads \
	--disable-os2threads \
	--disable-debug \
	--disable-stripping \
	--disable-everything \
    --disable-asm \
    --enable-shared \
    --enable-static \
    --disable-muxers \
    --disable-demuxers \
    --disable-parsers \
    --disable-filters \
    --disable-hwaccels \
    --enable-decoder=rawvideo \
    --enable-encoder=rawvideo \
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=mjpeg \
    --enable-decoder=mjpeg \
    --enable-decoder=h264 \
    --enable-parser=h264 \
    --disable-network \
	--disable-dxva2 \
	--disable-vaapi \
	--disable-vda \
	--disable-vdpau \
    --disable-bzlib \
	--disable-iconv \
	--disable-xlib \
	--disable-zlib
emmake make clean
emmake make
emmake make install