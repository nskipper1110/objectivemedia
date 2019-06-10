/*
 * Copyright 2018 The Emscripten Authors.  All rights reserved.
 * Emscripten is available under two separate licenses, the MIT license and the
 * University of Illinois/NCSA Open Source License.  Both these licenses can be
 * found in the LICENSE file.
 */

#include <emscripten/emscripten.h>

int main()
{
  EM_ASM(
    FS.writeFile('testfile', 'a=1\nb=2\n');
    var stream = FS.open('testfile', 'a');
    fd = FS.write(stream, new Uint8Array([99, 61, 51]) /* c=3 */, 0, 3);

    if (FS.llseek(stream, 0, 1 /* SEEK_CUR */) === 11) {
      console.log("success");
    }
    FS.close(stream);
  );

  return 0;
}
