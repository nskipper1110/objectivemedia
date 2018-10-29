source ../../emsdk-portable/emsdk_env.sh
emmake make -f objectivemedia_js.mk clean
emmake make -f objectivemedia_js.mk && cp -f ./build/js/x86/objectivemedia.js* tests/