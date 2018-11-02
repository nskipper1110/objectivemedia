#Mac x86 FFMPEG configure command
CFLAGS=`freetype-config --cflags` LDFLAGS=`freetype-config --libs` PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig:/usr/lib/pkgconfig:/usr/X11/lib/pkgconfig ./configure --prefix=./build/mac/x86 \
    --enable-yasm \
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
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=mjpeg \
    --enable-decoder=mjpeg \
    --enable-encoder=g723_1 \
    --enable-decoder=g723_1 \
    --enable-indev=avfoundation \
    --target-os=darwin arch=i386 \
    --enable-cross-compile \
    --cc="gcc -m32"
make clean
make
make install

#Mac x64 FFMPEG configure command
CFLAGS=`freetype-config --cflags` LDFLAGS=`freetype-config --libs` \
PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig:/usr/lib/pkgconfig:/usr/X11/lib/pkgconfig ./configure --prefix=./build/mac/x64 \
    --enable-yasm \
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
    --enable-decoder=h263 \
    --enable-encoder=h263p \
    --enable-encoder=mjpeg \
    --enable-decoder=mjpeg \
    --enable-encoder=g723_1 \
    --enable-decoder=g723_1 \
    --enable-indev=avfoundation \
    --target-os=darwin arch=x86_64 \
    --enable-cross-compile \
    --cc="gcc -fPIC"
make clean
make
make install

