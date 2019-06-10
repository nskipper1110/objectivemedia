#Mac x86 FFMPEG configure command
emconfigure ./configure --prefix=./build/js/x86 \
    --target-os=none arch=x86 \
    --enable-cross-compile \
    --cc="emcc" \
    --ar="emar" \
    --extra-cflags="-llibc" \
    --disable-runtime-cpudetect \
    --disable-doc \
	--disable-asm \
	--disable-fast-unaligned \
	--disable-pthreads \
	--disable-w32threads \
	--disable-os2threads \
	--disable-debug \
	--disable-stripping \
	--disable-all \
    --disable-asm \
    --enable-shared \
    --enable-static \
    --disable-ffmpeg \
    --disable-ffplay \
    --disable-ffprobe \
    --disable-ffserver \
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