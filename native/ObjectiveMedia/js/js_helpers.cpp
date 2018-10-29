#include "js_helpers.h"

/**
 * A helper function which allows the caller to convert a byte array to an integer value in JS.
 */
EMSCRIPTEN_KEEPALIVE int js_Helpers_BytesToInt(void* b){
    int retval = 0;
    memcpy((void*) &retval, (void*) b, 4);
    return retval;
}