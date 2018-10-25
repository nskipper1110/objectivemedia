source ../../emsdk-portable/emsdk_env.sh
emmake make -f objectivemedia_js.mk clean
emmake make -f objectivemedia_js.mk && cp -f objectivemedia.js* tests/