PATH="/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/bin":$PATH
make -f objectivemedia_mingw_x86.mk clean
make -f objectivemedia_mingw_x86.mk
cp -f "/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/bin/libgcc_s_dw2-1.dll" "../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x86/"
cp -f "/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/bin/libstdc++-6.dll" "../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x86/"
cp -f "/c/Program Files (x86)/mingw-w64/i686-6.1.0-posix-dwarf-rt_v5-rev0/mingw32/bin/libwinpthread-1.dll" "../../Java/com.mti.primitives/com.mti.primitives/src/com/mti/primitives/os/win/x86/"