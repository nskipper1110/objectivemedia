<<<<<<< HEAD
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
=======
../emsdk-portable/emsdk install latest
../emsdk-portable/emsdk activate latest
source ../emsdk-portable/emsdk_env.sh
cd $HOME/Projects/ffmpeg
mkdir -p $HOME/Projects/objectivemedia/ffmpeg/build/js/x86
emconfigure ./configure --prefix=$HOME/Projects/objectivemedia/ffmpeg/build/js/x86 \
    --target-os=none arch=x86 \
    --enable-cross-compile \
    --cc="emcc" \
	--extra-cflags="-s ERROR_ON_UNDEFINED_SYMBOLS=0" \
    --disable-runtime-cpudetect \
    --disable-doc \
	--disable-asm \
    --enable-gpl \
>>>>>>> deec8c204695cd10d4b54267080234bd789ee210
	--disable-fast-unaligned \
	--disable-pthreads \
	--disable-w32threads \
	--disable-os2threads \
	--disable-debug \
	--disable-stripping \
<<<<<<< HEAD
	--disable-all \
    --disable-asm \
    --enable-shared \
    --enable-static \
    --disable-ffmpeg \
    --disable-ffplay \
    --disable-ffprobe \
    --disable-ffserver \
=======
	--disable-everything \
    --disable-asm \
    --enable-shared \
    --enable-static \
>>>>>>> deec8c204695cd10d4b54267080234bd789ee210
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
<<<<<<< HEAD
    --disable-network \
	--disable-dxva2 \
	--disable-vaapi \
	--disable-vda \
=======
    --enable-decoder=h264 \
    --enable-parser=h264 \
    --enable-cuda \
    --enable-cuvid \
    --enable-nvenc \
    --disable-network \
	--disable-dxva2 \
	--disable-vaapi \
>>>>>>> deec8c204695cd10d4b54267080234bd789ee210
	--disable-vdpau \
    --disable-bzlib \
	--disable-iconv \
	--disable-xlib \
	--disable-zlib
emmake make clean
emmake make
emmake make install