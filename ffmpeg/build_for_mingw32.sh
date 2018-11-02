PATH="/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/bin":$PATH
#Windows x86 FFMPEG configure command using mingw32
./configure --prefix=./build/win/x86 \
            --disable-yasm \
            --disable-shared \
            --enable-static \
            --disable-ffmpeg \
            --disable-ffplay \
            --disable-ffprobe \
            --disable-ffserver \
            --disable-everything \
            --disable-muxers \
            --disable-demuxers \
            --disable-parsers \
            --disable-filters \
            --disable-hwaccels \
            --enable-decoder=rawvideo \
            --enable-encoder=rawvideo \
            --enable-demuxer=asf \
            --enable-muxer=asf \
            --enable-decoder=h263 \
            --enable-encoder=h263p \
            --enable-encoder=mjpeg \
            --enable-decoder=mjpeg \
            --enable-encoder=g723_1 \
            --enable-decoder=g723_1 \
            --enable-indev=dshow \
            --target-os=mingw32 \
            --arch=x86 \
            --enable-cross-compile \
            --cc="gcc -m32"
make clean
make
make install

