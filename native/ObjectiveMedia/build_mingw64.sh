PATH="/c/Program Files/mingw-w64/x86_64-6.1.0-posix-seh-rt_v5-rev0/mingw64/bin":$PATH
make -f objectivemedia_mingw_x64.mk clean
make -f objectivemedia_mingw_x64.mk
cp -f "/c/Program Files/mingw-w64/x86_64-6.1.0-posix-seh-rt_v5-rev0/mingw64/bin/libgcc_s_seh-1.dll" "../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x64/"
cp -f "/c/Program Files/mingw-w64/x86_64-6.1.0-posix-seh-rt_v5-rev0/mingw64/bin/libstdc++-6.dll" "../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x64/"
cp -f "/c/Program Files/mingw-w64/x86_64-6.1.0-posix-seh-rt_v5-rev0/mingw64/bin/libwinpthread-1.dll" "../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x64/"