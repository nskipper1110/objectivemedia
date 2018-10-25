/*
 * Copyright 2017 The Emscripten Authors.  All rights reserved.
 * Emscripten is available under two separate licenses, the MIT license and the
 * University of Illinois/NCSA Open Source License.  Both these licenses can be
 * found in the LICENSE file.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include "emscripten.h"

int get_TOTAL_MEMORY() {
  return EM_ASM_INT({ return TOTAL_MEMORY });
}

typedef void* voidStar;

int main(int argc, char **argv)
{
  int totalMemory = get_TOTAL_MEMORY();
  int chunk = 1024*1024;
  volatile voidStar alloc;
#ifdef FAIL_REALLOC_BUFFER
  EM_ASM({
    Module.seenOurReallocBuffer = false;
    Module['reallocBuffer'] = function() {
      Module.seenOurReallocBuffer = true;
      return null;
    };
  });
#endif
  for (int i = 0; i < (totalMemory/chunk)+2; i++) {
    // make sure state remains the same if malloc fails
    void* sbrk_before = sbrk(0);
    alloc = malloc(chunk);
    printf("%d : %d\n", i, !!alloc);
    if (alloc == NULL) {
      assert(sbrk(0) == sbrk_before);
      assert(totalMemory == get_TOTAL_MEMORY());
      break;
    }
  }
  assert(alloc == NULL);
#ifdef FAIL_REALLOC_BUFFER
  EM_ASM({
    assert(Module.seenOurReallocBuffer, 'our override should have been called');
  });
#endif
  puts("ok.");
  return 0;
}
