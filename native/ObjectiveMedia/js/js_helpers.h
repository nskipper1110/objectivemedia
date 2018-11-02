#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <emscripten.h>
#ifdef __cplusplus
extern "C" {
#endif
/**
 * A helper function which allows the caller to convert a byte array to an integer value in JS.
 */
EMSCRIPTEN_KEEPALIVE int js_Helpers_BytesToInt(void* b);
#ifdef __cplusplus
}
#endif