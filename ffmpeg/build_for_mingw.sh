#Windows x86 FFMPEG configure command using mingw32
./configure --arch=x86 --target-os=mingw32 --cross-prefix=x86_64-w64-mingw32- --pkg-config=pkg-config --prefix=./build/win/x86 --disable-yasm --disable-shared --enable-static --disable-ffmpeg --disable-ffplay --disable-ffprobe --disable-ffserver --disable-everything --disable-muxers --disable-demuxers --disable-parsers --disable-filters --disable-hwaccels --enable-decoder=rawvideo --enable-encoder=rawvideo --enable-decoder=h263 --enable-encoder=h263p --enable-encoder=g723_1 --enable-decoder=g723_1 --enable-indev=vfwcap --enable-cross-compile --cc="gcc -m32"
make clean
make
make install

#Windows x64 FFMPEG configure command using mingw32
./configure --arch=x86_64 --target-os=mingw32 --cross-prefix=x86_64-w64-mingw32- --pkg-config=pkg-config --prefix=./build/win/x64 --disable-yasm --disable-shared --enable-static --disable-ffmpeg --disable-ffplay --disable-ffprobe --disable-ffserver --disable-everything --disable-muxers --disable-demuxers --disable-parsers --disable-filters --disable-hwaccels \
 --enable-decoder=rawvideo --enable-encoder=rawvideo --enable-decoder=h263 --enable-encoder=h263p --enable-encoder=g723_1 --enable-decoder=g723_1 --enable-indev=vfwcap --enable-cross-compile --cc="gcc -m64 -fPIC"
make clean
make
make install

