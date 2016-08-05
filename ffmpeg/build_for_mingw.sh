<<<<<<< HEAD

=======
<<<<<<< HEAD
#Windows x86 FFMPEG configure command using mingw32
./configure --arch=x86 --target-os=mingw32 --cross-prefix=x86_64-w64-mingw32- --pkg-config=pkg-config --prefix=./build/win/x86 --disable-yasm --disable-shared --enable-static --disable-ffmpeg --disable-ffplay --disable-ffprobe --disable-ffserver --disable-everything --disable-muxers --disable-demuxers --disable-parsers --disable-filters --disable-hwaccels --enable-decoder=rawvideo --enable-encoder=rawvideo --enable-decoder=h263 --enable-encoder=h263p --enable-encoder=g723_1 --enable-decoder=g723_1 --enable-indev=vfwcap --enable-cross-compile --cc="gcc -m32"
make clean
make
make install

#Windows x64 FFMPEG configure command using mingw32
./configure --arch=x86_64 --target-os=mingw32 --cross-prefix=x86_64-w64-mingw32- --pkg-config=pkg-config --prefix=./build/win/x64 --disable-yasm --disable-shared --enable-static --disable-ffmpeg --disable-ffplay --disable-ffprobe --disable-ffserver --disable-everything --disable-muxers --disable-demuxers --disable-parsers --disable-filters --disable-hwaccels \
 --enable-decoder=rawvideo --enable-encoder=rawvideo --enable-decoder=h263 --enable-encoder=h263p --enable-encoder=g723_1 --enable-decoder=g723_1 --enable-indev=vfwcap --enable-cross-compile --cc="gcc -m64 -fPIC"
=======
>>>>>>> b3c912f41532d7fdc20c4e2469fba06c5fedbb36
PATH="/c/Program Files/mingw-w64/x86_64-6.1.0-posix-seh-rt_v5-rev0/mingw64/bin":$PATH
#Windows x64 FFMPEG configure command using mingw32
./configure --prefix=./build/win/x64 \
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
            --enable-encoder=g723_1 \
            --enable-decoder=g723_1 \
            --enable-indev=dshow \
            --target-os=mingw32 \
            --arch=x86_64 \
            --enable-cross-compile \
            --cc="gcc -m64 -fPIC"
>>>>>>> ce0552a01e9649381e1ea4cc97af4623fc30dc78
make clean
make
make install

