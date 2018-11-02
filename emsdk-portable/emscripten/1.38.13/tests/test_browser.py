# coding=utf-8
# Copyright 2013 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

from __future__ import print_function
import argparse
import json
import multiprocessing
import os
import random
import re
import shlex
import shutil
import subprocess
import time
import unittest
import webbrowser
import zlib

from runner import BrowserCore, path_from_root, has_browser, EMTEST_BROWSER
from tools import system_libs
from tools.shared import PYTHON, EMCC, WINDOWS, FILE_PACKAGER, PIPE, SPIDERMONKEY_ENGINE, JS_ENGINES
from tools.shared import try_delete, Building, run_process, run_js

try:
  from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
  # Python 2 compatibility
  from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


def test_chunked_synchronous_xhr_server(support_byte_ranges, chunkSize, data, checksum, port):
  class ChunkedServerHandler(BaseHTTPRequestHandler):
    def sendheaders(s, extra=[], length=len(data)):
      s.send_response(200)
      s.send_header("Content-Length", str(length))
      s.send_header("Access-Control-Allow-Origin", "http://localhost:%s" % port)
      s.send_header("Access-Control-Expose-Headers", "Content-Length, Accept-Ranges")
      s.send_header("Content-type", "application/octet-stream")
      if support_byte_ranges:
        s.send_header("Accept-Ranges", "bytes")
      for i in extra:
        s.send_header(i[0], i[1])
      s.end_headers()

    def do_HEAD(s):
      s.sendheaders()

    def do_OPTIONS(s):
      s.sendheaders([("Access-Control-Allow-Headers", "Range")], 0)

    def do_GET(s):
      if not support_byte_ranges:
        s.sendheaders()
        s.wfile.write(data)
      else:
        start, end = s.headers.get("range").split("=")[1].split("-")
        start = int(start)
        end = int(end)
        end = min(len(data) - 1, end)
        length = end - start + 1
        s.sendheaders([], length)
        s.wfile.write(data[start:end + 1])

  # CORS preflight makes OPTIONS requests which we need to account for.
  expectedConns = 22
  httpd = HTTPServer(('localhost', 11111), ChunkedServerHandler)
  for i in range(expectedConns + 1):
    httpd.handle_request()


def shell_with_script(shell_file, output_file, replacement):
  with open(path_from_root('src', shell_file)) as input:
    with open(output_file, 'w') as output:
      output.write(input.read().replace('{{{ SCRIPT }}}', replacement))


def is_chrome():
  return EMTEST_BROWSER and 'chrom' in EMTEST_BROWSER.lower()


def no_chrome(note='chome is not supported'):
  if is_chrome():
    return unittest.skip(note)
  return lambda f: f


def no_swiftshader(f):
  def decorated(self):
    if is_chrome() and '--use-gl=swiftshader' in EMTEST_BROWSER:
      self.skipTest('not compatible with swiftshader')
    return f(self)

  return decorated


requires_graphics_hardware = unittest.skipIf(os.getenv('EMTEST_LACKS_GRAPHICS_HARDWARE'), "This test requires graphics hardware")
requires_sound_hardware = unittest.skipIf(os.getenv('EMTEST_LACKS_SOUND_HARDWARE'), "This test requires sound hardware")


class browser(BrowserCore):
  @classmethod
  def setUpClass(self):
    super(browser, self).setUpClass()
    self.browser_timeout = 20
    print()
    print('Running the browser tests. Make sure the browser allows popups from localhost.')
    print()

  def test_sdl1_in_emscripten_nonstrict_mode(self):
    if 'EMCC_STRICT' in os.environ and int(os.environ['EMCC_STRICT']):
      self.skipTest('This test requires being run in non-strict mode (EMCC_STRICT env. variable unset)')
    # TODO: This test is verifying behavior that will be deprecated at some point in the future, remove this test once
    # system JS libraries are no longer automatically linked to anymore.
    self.btest('hello_world_sdl.cpp', reference='htmltest.png')

  def test_sdl1(self):
    self.btest('hello_world_sdl.cpp', reference='htmltest.png', args=['-lSDL', '-lGL'])
    self.btest('hello_world_sdl.cpp', reference='htmltest.png', args=['-s', 'USE_SDL=1', '-lGL']) # is the default anyhow

  # Deliberately named as test_zzz_* to make this test the last one
  # as this test may take the focus away from the main test window
  # by opening a new window and possibly not closing it.
  def test_zzz_html_source_map(self):
    if not has_browser():
      self.skipTest('need a browser')
    cpp_file = os.path.join(self.get_dir(), 'src.cpp')
    html_file = os.path.join(self.get_dir(), 'src.html')
    # browsers will try to 'guess' the corresponding original line if a
    # generated line is unmapped, so if we want to make sure that our
    # numbering is correct, we need to provide a couple of 'possible wrong
    # answers'. thus, we add some printf calls so that the cpp file gets
    # multiple mapped lines. in other words, if the program consists of a
    # single 'throw' statement, browsers may just map any thrown exception to
    # that line, because it will be the only mapped line.
    with open(cpp_file, 'w') as f:
      f.write(r'''
      #include <cstdio>

      int main() {
        printf("Starting test\n");
        try {
          throw 42; // line 8
        } catch (int e) { }
        printf("done\n");
        return 0;
      }
      ''')
    # use relative paths when calling emcc, because file:// URIs can only load
    # sourceContent when the maps are relative paths
    try_delete(html_file)
    try_delete(html_file + '.map')
    run_process([PYTHON, EMCC, 'src.cpp', '-o', 'src.html', '-g4', '-s', 'WASM=0'], cwd=self.get_dir())
    assert os.path.exists(html_file)
    assert os.path.exists(html_file + '.map')
    webbrowser.open_new('file://' + html_file)
    print('''
If manually bisecting:
  Check that you see src.cpp among the page sources.
  Even better, add a breakpoint, e.g. on the printf, then reload, then step
  through and see the print (best to run with EMTEST_SAVE_DIR=1 for the reload).
''')

  def test_emscripten_log(self):
    # TODO: wasm support for source maps
    src = os.path.join(self.get_dir(), 'src.cpp')
    open(src, 'w').write(self.with_report_result(open(path_from_root('tests', 'emscripten_log', 'emscripten_log.cpp')).read()))

    run_process([PYTHON, EMCC, src, '--pre-js', path_from_root('src', 'emscripten-source-map.min.js'), '-g', '-o', 'page.html', '-s', 'DEMANGLE_SUPPORT=1', '-s', 'WASM=0'])
    self.run_browser('page.html', None, '/report_result?1')

  def build_native_lzma(self):
    lzma_native = path_from_root('third_party', 'lzma.js', 'lzma-native')
    if os.path.isfile(lzma_native) and os.access(lzma_native, os.X_OK):
      return

    cwd = os.getcwd()
    try:
      os.chdir(path_from_root('third_party', 'lzma.js'))
      # On Windows prefer using MinGW make if it exists, otherwise fall back to hoping we have cygwin make.
      if WINDOWS and Building.which('mingw32-make'):
        run_process(['doit.bat'])
      else:
        run_process(['sh', './doit.sh'])
    finally:
      os.chdir(cwd)

  def test_preload_file(self):
    absolute_src_path = os.path.join(self.get_dir(), 'somefile.txt').replace('\\', '/')
    open(absolute_src_path, 'w').write('''load me right before running the code please''')

    absolute_src_path2 = os.path.join(self.get_dir(), '.somefile.txt').replace('\\', '/')
    open(absolute_src_path2, 'w').write('''load me right before running the code please''')

    absolute_src_path3 = os.path.join(self.get_dir(), 'some@file.txt').replace('\\', '/')
    open(absolute_src_path3, 'w').write('''load me right before running the code please''')

    def make_main(path):
      print('make main at', path)
      path = path.replace('\\', '\\\\').replace('"', '\\"') # Escape tricky path name for use inside a C string.
      open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
        #include <stdio.h>
        #include <string.h>
        #include <emscripten.h>
        int main() {
          FILE *f = fopen("%s", "r");
          char buf[100];
          fread(buf, 1, 20, f);
          buf[20] = 0;
          fclose(f);
          printf("|%%s|\n", buf);

          int result = !strcmp("load me right before", buf);
          REPORT_RESULT(result);
          return 0;
        }
        ''' % path))

    test_cases = [
      # (source preload-file string, file on target FS to load)
      ("somefile.txt", "somefile.txt"),
      (".somefile.txt@somefile.txt", "somefile.txt"),
      ("./somefile.txt", "somefile.txt"),
      ("somefile.txt@file.txt", "file.txt"),
      ("./somefile.txt@file.txt", "file.txt"),
      ("./somefile.txt@./file.txt", "file.txt"),
      ("somefile.txt@/file.txt", "file.txt"),
      ("somefile.txt@/", "somefile.txt"),
      (absolute_src_path + "@file.txt", "file.txt"),
      (absolute_src_path + "@/file.txt", "file.txt"),
      (absolute_src_path + "@/", "somefile.txt"),
      ("somefile.txt@/directory/file.txt", "/directory/file.txt"),
      ("somefile.txt@/directory/file.txt", "directory/file.txt"),
      (absolute_src_path + "@/directory/file.txt", "directory/file.txt"),
      ("some@@file.txt@other.txt", "other.txt"),
      ("some@@file.txt@some@@otherfile.txt", "some@otherfile.txt")]

    for test in test_cases:
      (srcpath, dstpath) = test
      print('Testing', srcpath, dstpath)
      make_main(dstpath)
      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', srcpath, '-o', 'page.html'])
      self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')
    # Test that '--no-heap-copy' works.
    if WINDOWS:
      # On Windows, the following non-alphanumeric non-control code ASCII characters are supported.
      # The characters <, >, ", |, ?, * are not allowed, because the Windows filesystem doesn't support those.
      tricky_filename = '!#$%&\'()+,-. ;=@[]^_`{}~.txt'
    else:
      # All 7-bit non-alphanumeric non-control code ASCII characters except /, : and \ are allowed.
      tricky_filename = '!#$%&\'()+,-. ;=@[]^_`{}~ "*<>?|.txt'
    open(os.path.join(self.get_dir(), tricky_filename), 'w').write('''load me right before running the code please''')
    make_main(tricky_filename)
    # As an Emscripten-specific feature, the character '@' must be escaped in the form '@@' to not confuse with the 'src@dst' notation.
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', tricky_filename.replace('@', '@@'), '--no-heap-copy', '-o', 'page.html'])
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')

    # By absolute path

    make_main('somefile.txt') # absolute becomes relative
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', absolute_src_path, '-o', 'page.html'])
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')

    # Test subdirectory handling with asset packaging.
    try_delete(self.in_dir('assets'))
    os.makedirs(os.path.join(self.get_dir(), 'assets/sub/asset1/').replace('\\', '/'))
    os.makedirs(os.path.join(self.get_dir(), 'assets/sub/asset1/.git').replace('\\', '/')) # Test adding directory that shouldn't exist.
    os.makedirs(os.path.join(self.get_dir(), 'assets/sub/asset2/').replace('\\', '/'))
    open(os.path.join(self.get_dir(), 'assets/sub/asset1/file1.txt'), 'w').write('''load me right before running the code please''')
    open(os.path.join(self.get_dir(), 'assets/sub/asset1/.git/shouldnt_be_embedded.txt'), 'w').write('''this file should not get embedded''')
    open(os.path.join(self.get_dir(), 'assets/sub/asset2/file2.txt'), 'w').write('''load me right before running the code please''')
    absolute_assets_src_path = os.path.join(self.get_dir(), 'assets').replace('\\', '/')

    def make_main_two_files(path1, path2, nonexistingpath):
      open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
        #include <stdio.h>
        #include <string.h>
        #include <emscripten.h>
        int main() {
          FILE *f = fopen("%s", "r");
          char buf[100];
          fread(buf, 1, 20, f);
          buf[20] = 0;
          fclose(f);
          printf("|%%s|\n", buf);

          int result = !strcmp("load me right before", buf);

          f = fopen("%s", "r");
          if (f == NULL)
            result = 0;
          fclose(f);

          f = fopen("%s", "r");
          if (f != NULL)
            result = 0;

          REPORT_RESULT(result);
          return 0;
        }
      ''' % (path1, path2, nonexistingpath)))

    test_cases = [
      # (source directory to embed, file1 on target FS to load, file2 on target FS to load, name of a file that *shouldn't* exist on VFS)
      ("assets", "assets/sub/asset1/file1.txt", "assets/sub/asset2/file2.txt", "assets/sub/asset1/.git/shouldnt_be_embedded.txt"),
      ("assets/", "assets/sub/asset1/file1.txt", "assets/sub/asset2/file2.txt", "assets/sub/asset1/.git/shouldnt_be_embedded.txt"),
      ("assets@/", "/sub/asset1/file1.txt", "/sub/asset2/file2.txt", "/sub/asset1/.git/shouldnt_be_embedded.txt"),
      ("assets/@/", "/sub/asset1/file1.txt", "/sub/asset2/file2.txt", "/sub/asset1/.git/shouldnt_be_embedded.txt"),
      ("assets@./", "/sub/asset1/file1.txt", "/sub/asset2/file2.txt", "/sub/asset1/.git/shouldnt_be_embedded.txt"),
      (absolute_assets_src_path + "@/", "/sub/asset1/file1.txt", "/sub/asset2/file2.txt", "/sub/asset1/.git/shouldnt_be_embedded.txt"),
      (absolute_assets_src_path + "@/assets", "/assets/sub/asset1/file1.txt", "/assets/sub/asset2/file2.txt", "assets/sub/asset1/.git/shouldnt_be_embedded.txt")]

    for test in test_cases:
      (srcpath, dstpath1, dstpath2, nonexistingpath) = test
      make_main_two_files(dstpath1, dstpath2, nonexistingpath)
      print(srcpath)
      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', srcpath, '--exclude-file', '*/.*', '-o', 'page.html'])
      self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')

    # Should still work with -o subdir/..

    make_main('somefile.txt') # absolute becomes relative
    try:
      os.mkdir(os.path.join(self.get_dir(), 'dirrey'))
    except:
      pass
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', absolute_src_path, '-o', 'dirrey/page.html'])
    self.run_browser('dirrey/page.html', 'You should see |load me right before|.', '/report_result?1')

    # With FS.preloadFile

    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      Module.preRun = function() {
        FS.createPreloadedFile('/', 'someotherfile.txt', 'somefile.txt', true, false); // we need --use-preload-plugins for this.
      };
    ''')
    make_main('someotherfile.txt')
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--pre-js', 'pre.js', '-o', 'page.html', '--use-preload-plugins'])
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')

  # Tests that user .html shell files can manually download .data files created with --preload-file cmdline.
  def test_preload_file_with_manual_data_download(self):
    src = os.path.join(self.get_dir(), 'src.cpp')
    open(src, 'w').write(self.with_report_result(open(os.path.join(path_from_root('tests/manual_download_data.cpp'))).read()))

    data = os.path.join(self.get_dir(), 'file.txt')
    open(data, 'w').write('''Hello!''')

    run_process([PYTHON, EMCC, 'src.cpp', '-o', 'manual_download_data.js', '--preload-file', data + '@/file.txt'])
    shutil.copyfile(path_from_root('tests', 'manual_download_data.html'), os.path.join(self.get_dir(), 'manual_download_data.html'))
    self.run_browser('manual_download_data.html', 'Hello!', '/report_result?1')

  # Tests that if the output files have single or double quotes in them, that it will be handled by correctly escaping the names.
  def test_output_file_escaping(self):
    tricky_part = '\'' if WINDOWS else '\' and \"' # On Windows, files/directories may not contain a double quote character. On non-Windowses they can, so test that.

    d = 'dir with ' + tricky_part
    abs_d = os.path.join(self.get_dir(), d)
    try:
      os.mkdir(abs_d)
    except:
      pass
    txt = 'file with ' + tricky_part + '.txt'
    abs_txt = os.path.join(abs_d, txt)
    open(abs_txt, 'w').write('load me right before')

    cpp = os.path.join(d, 'file with ' + tricky_part + '.cpp')
    open(cpp, 'w').write(self.with_report_result(r'''
      #include <stdio.h>
      #include <string.h>
      #include <emscripten.h>
      int main() {
        FILE *f = fopen("%s", "r");
        char buf[100];
        fread(buf, 1, 20, f);
        buf[20] = 0;
        fclose(f);
        printf("|%%s|\n", buf);
        int result = !strcmp("|load me right before|", buf);
        REPORT_RESULT(result);
        return 0;
      }
    ''' % (txt.replace('\'', '\\\'').replace('\"', '\\"'))))

    data_file = os.path.join(abs_d, 'file with ' + tricky_part + '.data')
    data_js_file = os.path.join(abs_d, 'file with ' + tricky_part + '.js')
    run_process([PYTHON, FILE_PACKAGER, data_file, '--use-preload-cache', '--indexedDB-name=testdb', '--preload', abs_txt + '@' + txt, '--js-output=' + data_js_file])
    page_file = os.path.join(d, 'file with ' + tricky_part + '.html')
    abs_page_file = os.path.join(self.get_dir(), page_file)
    run_process([PYTHON, EMCC, cpp, '--pre-js', data_js_file, '-o', abs_page_file, '-s', 'FORCE_FILESYSTEM=1'])
    self.run_browser(page_file, '|load me right before|.', '/report_result?0')

  def test_preload_caching(self):
    open(os.path.join(self.get_dir(), 'somefile.txt'), 'w').write('''load me right before running the code please''')

    def make_main(path):
      print(path)
      open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
        #include <stdio.h>
        #include <string.h>
        #include <emscripten.h>

        extern "C" {
          extern int checkPreloadResults();
        }

        int main(int argc, char** argv) {
          FILE *f = fopen("%s", "r");
          char buf[100];
          fread(buf, 1, 20, f);
          buf[20] = 0;
          fclose(f);
          printf("|%%s|\n", buf);

          int result = 0;

          result += !strcmp("load me right before", buf);
          result += checkPreloadResults();

          REPORT_RESULT(result);
          return 0;
        }
      ''' % path))

    open(os.path.join(self.get_dir(), 'test.js'), 'w').write('''
      mergeInto(LibraryManager.library, {
        checkPreloadResults: function() {
          var cached = 0;
          var packages = Object.keys(Module['preloadResults']);
          packages.forEach(function(package) {
            var fromCache = Module['preloadResults'][package]['fromCache'];
            if (fromCache)
              ++ cached;
          });
          return cached;
        }
      });
    ''')

    make_main('somefile.txt')
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--use-preload-cache', '--js-library', os.path.join(self.get_dir(), 'test.js'), '--preload-file', 'somefile.txt', '-o', 'page.html'])
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?2')

  def test_preload_caching_indexeddb_name(self):
    open(os.path.join(self.get_dir(), 'somefile.txt'), 'w').write('''load me right before running the code please''')

    def make_main(path):
      print(path)
      open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
        #include <stdio.h>
        #include <string.h>
        #include <emscripten.h>

        extern "C" {
          extern int checkPreloadResults();
        }

        int main(int argc, char** argv) {
          FILE *f = fopen("%s", "r");
          char buf[100];
          fread(buf, 1, 20, f);
          buf[20] = 0;
          fclose(f);
          printf("|%%s|\n", buf);

          int result = 0;

          result += !strcmp("load me right before", buf);
          result += checkPreloadResults();

          REPORT_RESULT(result);
          return 0;
        }
      ''' % path))

    open(os.path.join(self.get_dir(), 'test.js'), 'w').write('''
      mergeInto(LibraryManager.library, {
        checkPreloadResults: function() {
          var cached = 0;
          var packages = Object.keys(Module['preloadResults']);
          packages.forEach(function(package) {
            var fromCache = Module['preloadResults'][package]['fromCache'];
            if (fromCache)
              ++ cached;
          });
          return cached;
        }
      });
    ''')

    make_main('somefile.txt')
    run_process([PYTHON, FILE_PACKAGER, os.path.join(self.get_dir(), 'somefile.data'), '--use-preload-cache', '--indexedDB-name=testdb', '--preload', os.path.join(self.get_dir(), 'somefile.txt'), '--js-output=' + os.path.join(self.get_dir(), 'somefile.js')])
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--js-library', os.path.join(self.get_dir(), 'test.js'), '--pre-js', 'somefile.js', '-o', 'page.html', '-s', 'FORCE_FILESYSTEM=1'])
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?1')
    self.run_browser('page.html', 'You should see |load me right before|.', '/report_result?2')

  def test_multifile(self):
    # a few files inside a directory
    self.clear()
    os.makedirs(os.path.join(self.get_dir(), 'subdirr'))
    os.makedirs(os.path.join(self.get_dir(), 'subdirr', 'moar'))
    open(os.path.join(self.get_dir(), 'subdirr', 'data1.txt'), 'w').write('''1214141516171819''')
    open(os.path.join(self.get_dir(), 'subdirr', 'moar', 'data2.txt'), 'w').write('''3.14159265358979''')
    open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
      #include <stdio.h>
      #include <string.h>
      #include <emscripten.h>
      int main() {
        char buf[17];

        FILE *f = fopen("subdirr/data1.txt", "r");
        fread(buf, 1, 16, f);
        buf[16] = 0;
        fclose(f);
        printf("|%s|\n", buf);
        int result = !strcmp("1214141516171819", buf);

        FILE *f2 = fopen("subdirr/moar/data2.txt", "r");
        fread(buf, 1, 16, f2);
        buf[16] = 0;
        fclose(f2);
        printf("|%s|\n", buf);
        result = result && !strcmp("3.14159265358979", buf);

        REPORT_RESULT(result);
        return 0;
      }
    '''))

    # by individual files
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', 'subdirr/data1.txt', '--preload-file', 'subdirr/moar/data2.txt', '-o', 'page.html'])
    self.run_browser('page.html', 'You should see two cool numbers', '/report_result?1')
    os.remove('page.html')

    # by directory, and remove files to make sure
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--preload-file', 'subdirr', '-o', 'page.html'])
    shutil.rmtree(os.path.join(self.get_dir(), 'subdirr'))
    self.run_browser('page.html', 'You should see two cool numbers', '/report_result?1')

  def test_custom_file_package_url(self):
    # a few files inside a directory
    self.clear()
    os.makedirs(os.path.join(self.get_dir(), 'subdirr'))
    os.makedirs(os.path.join(self.get_dir(), 'cdn'))
    open(os.path.join(self.get_dir(), 'subdirr', 'data1.txt'), 'w').write('''1214141516171819''')
    # change the file package base dir to look in a "cdn". note that normally you would add this in your own custom html file etc., and not by
    # modifying the existing shell in this manner
    open(self.in_dir('shell.html'), 'w').write(open(path_from_root('src', 'shell.html')).read().replace('var Module = {', 'var Module = { locateFile: function (path, prefix) {if (path.endsWith(".wasm")) {return prefix + path;} else {return "cdn/" + path;}}, '))
    open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
      #include <stdio.h>
      #include <string.h>
      #include <emscripten.h>
      int main() {
        char buf[17];

        FILE *f = fopen("subdirr/data1.txt", "r");
        fread(buf, 1, 16, f);
        buf[16] = 0;
        fclose(f);
        printf("|%s|\n", buf);
        int result = !strcmp("1214141516171819", buf);

        REPORT_RESULT(result);
        return 0;
      }
    '''))

    def test():
      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'shell.html', '--preload-file', 'subdirr/data1.txt', '-o', 'test.html'])
      shutil.move('test.data', os.path.join('cdn', 'test.data'))
      self.run_browser('test.html', '', '/report_result?1')

    test()

  def test_missing_data_throws_error(self):
    def setup(assetLocalization):
      self.clear()
      open(self.in_dir("data.txt"), "w").write('''data''')
      open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
        #include <stdio.h>
        #include <string.h>
        #include <emscripten.h>
        int main() {
          // This code should never be executed in terms of missing required dependency file.
          REPORT_RESULT(0);
          return 0;
        }
      '''))
      open(os.path.join(self.get_dir(), 'on_window_error_shell.html'), 'w').write(r'''
      <html>
          <center><canvas id='canvas' width='256' height='256'></canvas></center>
          <hr><div id='output'></div><hr>
          <script type='text/javascript'>
            window.onerror = function(error) {
              window.onerror = null;
              var result = error.indexOf("test.data") >= 0 ? 1 : 0;
              var xhr = new XMLHttpRequest();
              xhr.open('GET', 'http://localhost:8888/report_result?' + result, true);
              xhr.send();
              setTimeout(function() { window.close() }, 1000);
            }
            var Module = {
              locateFile: function (path, prefix) {if (path.endsWith(".wasm")) {return prefix + path;} else {return "''' + assetLocalization + r'''" + path;}},
              print: (function() {
                var element = document.getElementById('output');
                return function(text) { element.innerHTML += text.replace('\n', '<br>', 'g') + '<br>';};
              })(),
              canvas: document.getElementById('canvas')
            };
          </script>
          {{{ SCRIPT }}}
        </body>
      </html>''')

    def test():
      # test test missing file should run xhr.onload with status different than 200, 304 or 206
      setup("")
      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'on_window_error_shell.html', '--preload-file', 'data.txt', '-o', 'test.html'])
      shutil.move('test.data', 'missing.data')
      self.run_browser('test.html', '', '/report_result?1')

      # test unknown protocol should go through xhr.onerror
      setup("unknown_protocol://")
      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'on_window_error_shell.html', '--preload-file', 'data.txt', '-o', 'test.html'])
      self.run_browser('test.html', '', '/report_result?1')

      # test wrong protocol and port
      setup("https://localhost:8800/")
      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'on_window_error_shell.html', '--preload-file', 'data.txt', '-o', 'test.html'])
      self.run_browser('test.html', '', '/report_result?1')

    test()

    # TODO: CORS, test using a full url for locateFile
    # open(self.in_dir('shell.html'), 'w').write(open(path_from_root('src', 'shell.html')).read().replace('var Module = {', 'var Module = { locateFile: function (path) {return "http:/localhost:8888/cdn/" + path;}, '))
    # test()

  def test_sdl_swsurface(self):
    self.btest('sdl_swsurface.c', args=['-lSDL', '-lGL'], expected='1')

  def test_sdl_surface_lock_opts(self):
    # Test Emscripten-specific extensions to optimize SDL_LockSurface and SDL_UnlockSurface.
    self.btest('hello_world_sdl.cpp', reference='htmltest.png', message='You should see "hello, world!" and a colored cube.', args=['-DTEST_SDL_LOCK_OPTS', '-lSDL', '-lGL'])

  def test_sdl_image(self):
    # load an image file, get pixel data. Also O2 coverage for --preload-file, and memory-init
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.jpg'))
    open(os.path.join(self.get_dir(), 'sdl_image.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_image.c')).read()))

    for mem in [0, 1]:
      for dest, dirname, basename in [('screenshot.jpg', '/', 'screenshot.jpg'),
                                      ('screenshot.jpg@/assets/screenshot.jpg', '/assets', 'screenshot.jpg')]:
        run_process([
          PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_image.c'), '-o', 'page.html', '-O2', '-lSDL', '-lGL', '--memory-init-file', str(mem),
          '--preload-file', dest, '-DSCREENSHOT_DIRNAME="' + dirname + '"', '-DSCREENSHOT_BASENAME="' + basename + '"', '--use-preload-plugins'
        ])
        self.run_browser('page.html', '', '/report_result?600')

  def test_sdl_image_jpeg(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.jpeg'))
    open(os.path.join(self.get_dir(), 'sdl_image_jpeg.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_image.c')).read()))
    run_process([
      PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_image_jpeg.c'), '-o', 'page.html', '-lSDL', '-lGL',
      '--preload-file', 'screenshot.jpeg', '-DSCREENSHOT_DIRNAME="/"', '-DSCREENSHOT_BASENAME="screenshot.jpeg"', '--use-preload-plugins'
    ])
    self.run_browser('page.html', '', '/report_result?600')

  def test_sdl_image_prepare(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_image_prepare.c', reference='screenshot.jpg', args=['--preload-file', 'screenshot.not', '-lSDL', '-lGL'], also_proxied=True)

  def test_sdl_image_prepare_data(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_image_prepare_data.c', reference='screenshot.jpg', args=['--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

  def test_sdl_image_must_prepare(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.jpg'))
    self.btest('sdl_image_must_prepare.c', reference='screenshot.jpg', args=['--preload-file', 'screenshot.jpg', '-lSDL', '-lGL'])

  def test_sdl_stb_image(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image.c', reference='screenshot.jpg', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

  def test_sdl_stb_image_bpp(self):
    # load grayscale image without alpha
    self.clear()
    shutil.copyfile(path_from_root('tests', 'sdl-stb-bpp1.png'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image.c', reference='sdl-stb-bpp1.png', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

    # load grayscale image with alpha
    self.clear()
    shutil.copyfile(path_from_root('tests', 'sdl-stb-bpp2.png'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image.c', reference='sdl-stb-bpp2.png', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

    # load RGB image
    self.clear()
    shutil.copyfile(path_from_root('tests', 'sdl-stb-bpp3.png'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image.c', reference='sdl-stb-bpp3.png', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

    # load RGBA image
    self.clear()
    shutil.copyfile(path_from_root('tests', 'sdl-stb-bpp4.png'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image.c', reference='sdl-stb-bpp4.png', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

  def test_sdl_stb_image_data(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image_data.c', reference='screenshot.jpg', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL'])

  def test_sdl_stb_image_cleanup(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl_stb_image_cleanup.c', expected='0', args=['-s', 'STB_IMAGE=1', '--preload-file', 'screenshot.not', '-lSDL', '-lGL', '--memoryprofiler'])

  def test_sdl_canvas(self):
    self.clear()
    self.btest('sdl_canvas.c', expected='1', args=['-s', 'LEGACY_GL_EMULATION=1', '-lSDL', '-lGL'])
    # some extra coverage
    self.clear()
    self.btest('sdl_canvas.c', expected='1', args=['-s', 'LEGACY_GL_EMULATION=1', '-O0', '-s', 'SAFE_HEAP=1', '-lSDL', '-lGL'])
    self.clear()
    self.btest('sdl_canvas.c', expected='1', args=['-s', 'LEGACY_GL_EMULATION=1', '-O2', '-s', 'SAFE_HEAP=1', '-lSDL', '-lGL'])

  def post_manual_reftest(self, reference=None):
    self.reftest(path_from_root('tests', self.reference if reference is None else reference))

    html = open('test.html').read()
    html = html.replace('</body>', '''
<script>
function assert(x, y) { if (!x) throw 'assertion failed ' + y }

%s

var windowClose = window.close;
window.close = function() {
  // wait for rafs to arrive and the screen to update before reftesting
  setTimeout(function() {
    doReftest();
    setTimeout(windowClose, 5000);
  }, 1000);
};
</script>
</body>''' % open('reftest.js').read())
    open('test.html', 'w').write(html)

  def test_sdl_canvas_proxy(self):
    open('data.txt', 'w').write('datum')
    self.btest('sdl_canvas_proxy.c', reference='sdl_canvas_proxy.png', args=['--proxy-to-worker', '--preload-file', 'data.txt', '-lSDL', '-lGL'], manual_reference=True, post_build=self.post_manual_reftest)

  @requires_graphics_hardware
  def test_glgears_proxy(self):
    # we modify the asm.js, this is a non-wasm test
    self.btest('hello_world_gles_proxy.c', reference='gears.png', args=['--proxy-to-worker', '-s', 'GL_TESTING=1', '-DSTATIC_GEARS=1', '-lGL', '-lglut', '-s', 'WASM=0'], manual_reference=True, post_build=self.post_manual_reftest)

    # test noProxy option applied at runtime

    # run normally (duplicates above test, but verifies we can run outside of the btest harness
    self.run_browser('test.html', None, ['/report_result?0'])

    # run with noProxy
    self.run_browser('test.html?noProxy', None, ['/report_result?0'])

    def copy(to, js_mod, html_mod=lambda x: x):
      open(to + '.html', 'w').write(html_mod(open('test.html').read().replace('test.js', to + '.js')))
      open(to + '.js', 'w').write(js_mod(open('test.js').read()))

    # run with noProxy, but make main thread fail
    copy('two', lambda original: re.sub(r'function _main\(\$(.+),\$(.+)\) {', r'function _main($\1,$\2) { if (ENVIRONMENT_IS_WEB) { var xhr = new XMLHttpRequest(); xhr.open("GET", "http://localhost:%s/report_result?999");xhr.send(); return; }' % self.test_port, original),
         lambda original: original.replace('function doReftest() {', 'function doReftest() { return; ')) # don't reftest on main thread, it would race
    self.run_browser('two.html?noProxy', None, ['/report_result?999'])
    copy('two', lambda original: re.sub(r'function _main\(\$(.+),\$(.+)\) {', r'function _main($\1,$\2) { if (ENVIRONMENT_IS_WEB) { var xhr = new XMLHttpRequest(); xhr.open("GET", "http://localhost:%s/report_result?999");xhr.send(); return; }' % self.test_port, original))
    self.run_browser('two.html', None, ['/report_result?0']) # this is still cool

    # run without noProxy, so proxy, but make worker fail
    copy('three', lambda original: re.sub(r'function _main\(\$(.+),\$(.+)\) {', r'function _main($\1,$\2) { if (ENVIRONMENT_IS_WORKER) { var xhr = new XMLHttpRequest(); xhr.open("GET", "http://localhost:%s/report_result?999");xhr.send(); return; }' % self.test_port, original),
         lambda original: original.replace('function doReftest() {', 'function doReftest() { return; ')) # don't reftest on main thread, it would race
    self.run_browser('three.html', None, ['/report_result?999'])
    copy('three', lambda original: re.sub(r'function _main\(\$(.+),\$(.+)\) {', r'function _main($\1,$\2) { if (ENVIRONMENT_IS_WORKER) { var xhr = new XMLHttpRequest(); xhr.open("GET", "http://localhost:%s/report_result?999");xhr.send(); return; }' % self.test_port, original))
    self.run_browser('three.html?noProxy', None, ['/report_result?0']) # this is still cool

  @requires_graphics_hardware
  def test_glgears_proxy_jstarget(self):
    # test .js target with --proxy-worker; emits 2 js files, client and worker
    run_process([PYTHON, EMCC, path_from_root('tests', 'hello_world_gles_proxy.c'), '-o', 'test.js', '--proxy-to-worker', '-s', 'GL_TESTING=1', '-lGL', '-lglut'])
    shell_with_script('shell_minimal.html', 'test.html', '<script src="test.js"></script>')
    self.post_manual_reftest('gears.png')
    self.run_browser('test.html', None, '/report_result?0')

  def test_sdl_canvas_alpha(self):
    # N.B. On Linux with Intel integrated graphics cards, this test needs Firefox 49 or newer.
    # See https://github.com/kripken/emscripten/issues/4069.
    open(os.path.join(self.get_dir(), 'flag_0.js'), 'w').write('''
      Module['arguments'] = ['-0'];
    ''')

    self.btest('sdl_canvas_alpha.c', args=['-lSDL', '-lGL'], reference='sdl_canvas_alpha.png', reference_slack=12)
    self.btest('sdl_canvas_alpha.c', args=['--pre-js', 'flag_0.js', '-lSDL', '-lGL'], reference='sdl_canvas_alpha_flag_0.png', reference_slack=12)

  def test_sdl_key(self):
    for delay in [0, 1]:
      for defines in [
        [],
        ['-DTEST_EMSCRIPTEN_SDL_SETEVENTHANDLER']
      ]:
        for emterps in [
          [],
          ['-DTEST_SLEEP', '-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-s', 'ASSERTIONS=1', '-s', "SAFE_HEAP=1"]
        ]:
          print(delay, defines, emterps)
          open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
            function keydown(c) {
             %s
              //out('push keydown');
              var event = document.createEvent("KeyboardEvent");
              event.initKeyEvent("keydown", true, true, window,
                                 0, 0, 0, 0,
                                 c, c);
              document.dispatchEvent(event);
             %s
            }

            function keyup(c) {
             %s
              //out('push keyup');
              var event = document.createEvent("KeyboardEvent");
              event.initKeyEvent("keyup", true, true, window,
                                 0, 0, 0, 0,
                                 c, c);
              document.dispatchEvent(event);
             %s
            }
          ''' % ('setTimeout(function() {' if delay else '', '}, 1);' if delay else '', 'setTimeout(function() {' if delay else '', '}, 1);' if delay else ''))
          open(os.path.join(self.get_dir(), 'sdl_key.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_key.c')).read()))

          run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_key.c'), '-o', 'page.html'] + defines + emterps + ['--pre-js', 'pre.js', '-s', '''EXPORTED_FUNCTIONS=['_main']''', '-lSDL', '-lGL'])
          self.run_browser('page.html', '', '/report_result?223092870')

  def test_sdl_key_proxy(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      var Module = {};
      Module.postRun = function() {
        function doOne() {
          Module._one();
          setTimeout(doOne, 1000/60);
        }
        setTimeout(doOne, 1000/60);
      }
    ''')

    def post():
      html = open('test.html').read()
      html = html.replace('</body>', '''
<script>
function keydown(c) {
  var event = document.createEvent("KeyboardEvent");
  event.initKeyEvent("keydown", true, true, window,
                     0, 0, 0, 0,
                     c, c);
  document.dispatchEvent(event);
}

function keyup(c) {
  var event = document.createEvent("KeyboardEvent");
  event.initKeyEvent("keyup", true, true, window,
                     0, 0, 0, 0,
                     c, c);
  document.dispatchEvent(event);
}

keydown(1250);keydown(38);keyup(38);keyup(1250); // alt, up
keydown(1248);keydown(1249);keydown(40);keyup(40);keyup(1249);keyup(1248); // ctrl, shift, down
keydown(37);keyup(37); // left
keydown(39);keyup(39); // right
keydown(65);keyup(65); // a
keydown(66);keyup(66); // b
keydown(100);keyup(100); // trigger the end

</script>
</body>''')
      open('test.html', 'w').write(html)

    self.btest('sdl_key_proxy.c', '223092870', args=['--proxy-to-worker', '--pre-js', 'pre.js', '-s', '''EXPORTED_FUNCTIONS=['_main', '_one']''', '-lSDL', '-lGL'], manual_reference=True, post_build=post)

  def test_keydown_preventdefault_proxy(self):
    def post():
      html = open('test.html').read()
      html = html.replace('</body>', '''
<script>
function keydown(c) {
  var event = document.createEvent("KeyboardEvent");
  event.initKeyEvent("keydown", true, true, window,
                     0, 0, 0, 0,
                     c, c);
  return document.dispatchEvent(event);
}

function keypress(c) {
  var event = document.createEvent("KeyboardEvent");
  event.initKeyEvent("keypress", true, true, window,
                     0, 0, 0, 0,
                     c, c);
  return document.dispatchEvent(event);
}

function keyup(c) {
  var event = document.createEvent("KeyboardEvent");
  event.initKeyEvent("keyup", true, true, window,
                     0, 0, 0, 0,
                     c, c);
  return document.dispatchEvent(event);
}

function sendKey(c) {
  // Simulate the sending of the keypress event when the
  // prior keydown event is not prevent defaulted.
  if (keydown(c) === false) {
    console.log('keydown prevent defaulted, NOT sending keypress!!!');
  } else {
    keypress(c);
  }
  keyup(c);
}

// Send 'a'. Simulate the sending of the keypress event when the
// prior keydown event is not prevent defaulted.
sendKey(65);

// Send backspace. Keypress should not be sent over as default handling of
// the Keydown event should be prevented.
sendKey(8);

keydown(100);keyup(100); // trigger the end
</script>
</body>''')

      open('test.html', 'w').write(html)

    self.btest('keydown_preventdefault_proxy.cpp', '300', args=['--proxy-to-worker', '-s', '''EXPORTED_FUNCTIONS=['_main']'''], manual_reference=True, post_build=post)

  def test_sdl_text(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      Module.postRun = function() {
        function doOne() {
          Module._one();
          setTimeout(doOne, 1000/60);
        }
        setTimeout(doOne, 1000/60);
      }

      function simulateKeyEvent(charCode) {
        var event = document.createEvent("KeyboardEvent");
        event.initKeyEvent("keypress", true, true, window,
                           0, 0, 0, 0, 0, charCode);
        document.body.dispatchEvent(event);
      }
    ''')
    open(os.path.join(self.get_dir(), 'sdl_text.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_text.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_text.c'), '-o', 'page.html', '--pre-js', 'pre.js', '-s', '''EXPORTED_FUNCTIONS=['_main', '_one']''', '-lSDL', '-lGL'])
    self.run_browser('page.html', '', '/report_result?1')

  def test_sdl_mouse(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function simulateMouseEvent(x, y, button) {
        var event = document.createEvent("MouseEvents");
        if (button >= 0) {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousedown', true, true, window,
                     1, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event1);
          var event2 = document.createEvent("MouseEvents");
          event2.initMouseEvent('mouseup', true, true, window,
                     1, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event2);
        } else {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousemove', true, true, window,
                     0, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y,
                     0, 0, 0, 0,
                     0, null);
          Module['canvas'].dispatchEvent(event1);
        }
      }
      window['simulateMouseEvent'] = simulateMouseEvent;
    ''')
    open(os.path.join(self.get_dir(), 'sdl_mouse.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_mouse.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_mouse.c'), '-O2', '--minify', '0', '-o', 'page.html', '--pre-js', 'pre.js', '-lSDL', '-lGL'])
    self.run_browser('page.html', '', '/report_result?1')

  def test_sdl_mouse_offsets(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function simulateMouseEvent(x, y, button) {
        var event = document.createEvent("MouseEvents");
        if (button >= 0) {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousedown', true, true, window,
                     1, x, y, x, y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event1);
          var event2 = document.createEvent("MouseEvents");
          event2.initMouseEvent('mouseup', true, true, window,
                     1, x, y, x, y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event2);
        } else {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousemove', true, true, window,
                     0, x, y, x, y,
                     0, 0, 0, 0,
                     0, null);
          Module['canvas'].dispatchEvent(event1);
        }
      }
      window['simulateMouseEvent'] = simulateMouseEvent;
    ''')
    open(os.path.join(self.get_dir(), 'page.html'), 'w').write('''
      <html>
        <head>
          <style type="text/css">
            html, body { margin: 0; padding: 0; }
            #container {
              position: absolute;
              left: 5px; right: 0;
              top: 5px; bottom: 0;
            }
            #canvas {
              position: absolute;
              left: 0; width: 600px;
              top: 0; height: 450px;
            }
            textarea {
              margin-top: 500px;
              margin-left: 5px;
              width: 600px;
            }
          </style>
        </head>
        <body>
          <div id="container">
            <canvas id="canvas"></canvas>
          </div>
          <textarea id="output" rows="8"></textarea>
          <script type="text/javascript">
            var Module = {
              canvas: document.getElementById('canvas'),
              print: (function() {
                var element = document.getElementById('output');
                element.value = ''; // clear browser cache
                return function(text) {
                  if (arguments.length > 1) text = Array.prototype.slice.call(arguments).join(' ');
                  element.value += text + "\\n";
                  element.scrollTop = element.scrollHeight; // focus on bottom
                };
              })()
            };
          </script>
          <script type="text/javascript" src="sdl_mouse.js"></script>
        </body>
      </html>
    ''')
    open(os.path.join(self.get_dir(), 'sdl_mouse.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_mouse.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_mouse.c'), '-DTEST_SDL_MOUSE_OFFSETS', '-O2', '--minify', '0', '-o', 'sdl_mouse.js', '--pre-js', 'pre.js', '-lSDL', '-lGL'])
    self.run_browser('page.html', '', '/report_result?1')

  def test_glut_touchevents(self):
    self.btest('glut_touchevents.c', '1', args=['-lglut'])

  def test_glut_wheelevents(self):
    self.btest('glut_wheelevents.c', '1', args=['-lglut'])

  def test_sdl_joystick_1(self):
    # Generates events corresponding to the Working Draft of the HTML5 Gamepad API.
    # http://www.w3.org/TR/2012/WD-gamepad-20120529/#gamepad-interface
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      var gamepads = [];
      // Spoof this function.
      navigator['getGamepads'] = function() {
        return gamepads;
      };
      window['addNewGamepad'] = function(id, numAxes, numButtons) {
        var index = gamepads.length;
        gamepads.push({
          axes: new Array(numAxes),
          buttons: new Array(numButtons),
          id: id,
          index: index
        });
        var i;
        for (i = 0; i < numAxes; i++) gamepads[index].axes[i] = 0;
        for (i = 0; i < numButtons; i++) gamepads[index].buttons[i] = 0;
      };
      window['simulateGamepadButtonDown'] = function (index, button) {
        gamepads[index].buttons[button] = 1;
      };
      window['simulateGamepadButtonUp'] = function (index, button) {
        gamepads[index].buttons[button] = 0;
      };
      window['simulateAxisMotion'] = function (index, axis, value) {
        gamepads[index].axes[axis] = value;
      };
    ''')
    open(os.path.join(self.get_dir(), 'sdl_joystick.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_joystick.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_joystick.c'), '-O2', '--minify', '0', '-o', 'page.html', '--pre-js', 'pre.js', '-lSDL', '-lGL'])
    self.run_browser('page.html', '', '/report_result?2')

  def test_sdl_joystick_2(self):
    # Generates events corresponding to the Editor's Draft of the HTML5 Gamepad API.
    # https://dvcs.w3.org/hg/gamepad/raw-file/default/gamepad.html#idl-def-Gamepad
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      var gamepads = [];
      // Spoof this function.
      navigator['getGamepads'] = function() {
        return gamepads;
      };
      window['addNewGamepad'] = function(id, numAxes, numButtons) {
        var index = gamepads.length;
        gamepads.push({
          axes: new Array(numAxes),
          buttons: new Array(numButtons),
          id: id,
          index: index
        });
        var i;
        for (i = 0; i < numAxes; i++) gamepads[index].axes[i] = 0;
        // Buttons are objects
        for (i = 0; i < numButtons; i++) gamepads[index].buttons[i] = { pressed: false, value: 0 };
      };
      // FF mutates the original objects.
      window['simulateGamepadButtonDown'] = function (index, button) {
        gamepads[index].buttons[button].pressed = true;
        gamepads[index].buttons[button].value = 1;
      };
      window['simulateGamepadButtonUp'] = function (index, button) {
        gamepads[index].buttons[button].pressed = false;
        gamepads[index].buttons[button].value = 0;
      };
      window['simulateAxisMotion'] = function (index, axis, value) {
        gamepads[index].axes[axis] = value;
      };
    ''')
    open(os.path.join(self.get_dir(), 'sdl_joystick.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_joystick.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_joystick.c'), '-O2', '--minify', '0', '-o', 'page.html', '--pre-js', 'pre.js', '-lSDL', '-lGL'])
    self.run_browser('page.html', '', '/report_result?2')

  @requires_graphics_hardware
  def test_glfw_joystick(self):
    # Generates events corresponding to the Editor's Draft of the HTML5 Gamepad API.
    # https://dvcs.w3.org/hg/gamepad/raw-file/default/gamepad.html#idl-def-Gamepad
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      var gamepads = [];
      // Spoof this function.
      navigator['getGamepads'] = function() {
        return gamepads;
      };
      window['addNewGamepad'] = function(id, numAxes, numButtons) {
        var index = gamepads.length;
        var gamepad = {
          axes: new Array(numAxes),
          buttons: new Array(numButtons),
          id: id,
          index: index
        };
        gamepads.push(gamepad)
        var i;
        for (i = 0; i < numAxes; i++) gamepads[index].axes[i] = 0;
        // Buttons are objects
        for (i = 0; i < numButtons; i++) gamepads[index].buttons[i] = { pressed: false, value: 0 };

        // Dispatch event (required for glfw joystick; note not used in SDL test)
        var event = new Event('gamepadconnected');
        event.gamepad = gamepad;
        window.dispatchEvent(event);
      };
      // FF mutates the original objects.
      window['simulateGamepadButtonDown'] = function (index, button) {
        gamepads[index].buttons[button].pressed = true;
        gamepads[index].buttons[button].value = 1;
      };
      window['simulateGamepadButtonUp'] = function (index, button) {
        gamepads[index].buttons[button].pressed = false;
        gamepads[index].buttons[button].value = 0;
      };
      window['simulateAxisMotion'] = function (index, axis, value) {
        gamepads[index].axes[axis] = value;
      };
    ''')
    open(os.path.join(self.get_dir(), 'test_glfw_joystick.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'test_glfw_joystick.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'test_glfw_joystick.c'), '-O2', '--minify', '0', '-o', 'page.html', '--pre-js', 'pre.js', '-lGL', '-lglfw3', '-s', 'USE_GLFW=3'])
    self.run_browser('page.html', '', '/report_result?2')

  @requires_graphics_hardware
  def test_webgl_context_attributes(self):
    # Javascript code to check the attributes support we want to test in the WebGL implementation
    # (request the attribute, create a context and check its value afterwards in the context attributes).
    # Tests will succeed when an attribute is not supported.
    open(os.path.join(self.get_dir(), 'check_webgl_attributes_support.js'), 'w').write('''
      mergeInto(LibraryManager.library, {
        webglAntialiasSupported: function() {
          canvas = document.createElement('canvas');
          context = canvas.getContext('experimental-webgl', {antialias: true});
          attributes = context.getContextAttributes();
          return attributes.antialias;
        },
        webglDepthSupported: function() {
          canvas = document.createElement('canvas');
          context = canvas.getContext('experimental-webgl', {depth: true});
          attributes = context.getContextAttributes();
          return attributes.depth;
        },
        webglStencilSupported: function() {
          canvas = document.createElement('canvas');
          context = canvas.getContext('experimental-webgl', {stencil: true});
          attributes = context.getContextAttributes();
          return attributes.stencil;
        },
        webglAlphaSupported: function() {
          canvas = document.createElement('canvas');
          context = canvas.getContext('experimental-webgl', {alpha: true});
          attributes = context.getContextAttributes();
          return attributes.alpha;
        }
      });
    ''')

    # Copy common code file to temporary directory
    filepath = path_from_root('tests/test_webgl_context_attributes_common.c')
    temp_filepath = os.path.join(self.get_dir(), os.path.basename(filepath))
    shutil.copyfile(filepath, temp_filepath)

    # perform tests with attributes activated
    self.btest('test_webgl_context_attributes_glut.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-DAA_ACTIVATED', '-DDEPTH_ACTIVATED', '-DSTENCIL_ACTIVATED', '-DALPHA_ACTIVATED', '-lGL', '-lglut', '-lGLEW'])
    self.btest('test_webgl_context_attributes_sdl.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-DAA_ACTIVATED', '-DDEPTH_ACTIVATED', '-DSTENCIL_ACTIVATED', '-DALPHA_ACTIVATED', '-lGL', '-lSDL', '-lGLEW'])
    self.btest('test_webgl_context_attributes_sdl2.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-DAA_ACTIVATED', '-DDEPTH_ACTIVATED', '-DSTENCIL_ACTIVATED', '-DALPHA_ACTIVATED', '-lGL', '-s', 'USE_SDL=2', '-lGLEW'])
    self.btest('test_webgl_context_attributes_glfw.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-DAA_ACTIVATED', '-DDEPTH_ACTIVATED', '-DSTENCIL_ACTIVATED', '-DALPHA_ACTIVATED', '-lGL', '-lglfw', '-lGLEW'])

    # perform tests with attributes desactivated
    self.btest('test_webgl_context_attributes_glut.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-lGL', '-lglut', '-lGLEW'])
    self.btest('test_webgl_context_attributes_sdl.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-lGL', '-lSDL', '-lGLEW'])
    self.btest('test_webgl_context_attributes_glfw.c', '1', args=['--js-library', 'check_webgl_attributes_support.js', '-lGL', '-lglfw', '-lGLEW'])

  # Test that -s GL_PREINITIALIZED_CONTEXT=1 works and allows user to set Module['preinitializedWebGLContext'] to a preinitialized WebGL context.
  @requires_graphics_hardware
  def test_preinitialized_webgl_context(self):
    self.btest('preinitialized_webgl_context.cpp', '5', args=['-s', 'GL_PREINITIALIZED_CONTEXT=1', '--shell-file', path_from_root('tests/preinitialized_webgl_context.html')])

  def test_emscripten_get_now(self):
    self.btest('emscripten_get_now.cpp', '1')

  @unittest.skip('Skipping due to https://github.com/kripken/emscripten/issues/2770')
  def test_fflush(self):
    self.btest('test_fflush.cpp', '0', args=['--shell-file', path_from_root('tests', 'test_fflush.html')])

  def test_file_db(self):
    secret = str(time.time())
    open('moar.txt', 'w').write(secret)
    self.btest('file_db.cpp', '1', args=['--preload-file', 'moar.txt', '-DFIRST'])
    shutil.copyfile('test.html', 'first.html')
    self.btest('file_db.cpp', secret, args=['-s', 'FORCE_FILESYSTEM=1'])
    shutil.copyfile('test.html', 'second.html')
    open('moar.txt', 'w').write('aliantha')
    self.btest('file_db.cpp', secret, args=['--preload-file', 'moar.txt']) # even with a file there, we load over it
    shutil.move('test.html', 'third.html')

  def test_fs_idbfs_sync(self):
    for mode in [[], ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1']]:
      for extra in [[], ['-DEXTRA_WORK']]:
        secret = str(time.time())
        self.btest(path_from_root('tests', 'fs', 'test_idbfs_sync.c'), '1', force_c=True, args=mode + ['-lidbfs.js', '-DFIRST', '-DSECRET=\"' + secret + '\"', '-s', '''EXPORTED_FUNCTIONS=['_main', '_test', '_success']'''])
        self.btest(path_from_root('tests', 'fs', 'test_idbfs_sync.c'), '1', force_c=True, args=mode + ['-lidbfs.js', '-DSECRET=\"' + secret + '\"', '-s', '''EXPORTED_FUNCTIONS=['_main', '_test', '_success']'''] + extra)

  def test_fs_idbfs_fsync(self):
    # sync from persisted state into memory before main()
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      Module.preRun = function() {
        addRunDependency('syncfs');

        FS.mkdir('/working1');
        FS.mount(IDBFS, {}, '/working1');
        FS.syncfs(true, function (err) {
          if (err) throw err;
          removeRunDependency('syncfs');
        });
      };
    ''')

    args = ['--pre-js', 'pre.js', '-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-lidbfs.js', '-s', 'EXIT_RUNTIME=1']
    for mode in [[], ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1']]:
      secret = str(time.time())
      self.btest(path_from_root('tests', 'fs', 'test_idbfs_fsync.c'), '1', force_c=True, args=args + mode + ['-DFIRST', '-DSECRET=\"' + secret + '\"', '-s', '''EXPORTED_FUNCTIONS=['_main', '_success']'''])
      self.btest(path_from_root('tests', 'fs', 'test_idbfs_fsync.c'), '1', force_c=True, args=args + mode + ['-DSECRET=\"' + secret + '\"', '-s', '''EXPORTED_FUNCTIONS=['_main', '_success']'''])

  def test_fs_memfs_fsync(self):
    args = ['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-s', 'EXIT_RUNTIME=1']
    for mode in [[], ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1']]:
      secret = str(time.time())
      self.btest(path_from_root('tests', 'fs', 'test_memfs_fsync.c'), '1', force_c=True, args=args + mode + ['-DSECRET=\"' + secret + '\"', '-s', '''EXPORTED_FUNCTIONS=['_main']'''])

  def test_fs_workerfs_read(self):
    secret = 'a' * 10
    secret2 = 'b' * 10
    open(self.in_dir('pre.js'), 'w').write('''
      var Module = {};
      Module.preRun = function() {
        var blob = new Blob(['%s']);
        var file = new File(['%s'], 'file.txt');
        FS.mkdir('/work');
        FS.mount(WORKERFS, {
          blobs: [{ name: 'blob.txt', data: blob }],
          files: [file],
        }, '/work');
      };
    ''' % (secret, secret2))
    self.btest(path_from_root('tests', 'fs', 'test_workerfs_read.c'), '1', force_c=True, args=['-lworkerfs.js', '--pre-js', 'pre.js', '-DSECRET=\"' + secret + '\"', '-DSECRET2=\"' + secret2 + '\"', '--proxy-to-worker'])

  def test_fs_workerfs_package(self):
    open('file1.txt', 'w').write('first')
    if not os.path.exists('sub'):
      os.makedirs('sub')
    open(os.path.join('sub', 'file2.txt'), 'w').write('second')
    run_process([PYTHON, FILE_PACKAGER, 'files.data', '--preload', 'file1.txt', os.path.join('sub', 'file2.txt'), '--separate-metadata', '--js-output=files.js'])
    self.btest(os.path.join('fs', 'test_workerfs_package.cpp'), '1', args=['-lworkerfs.js', '--proxy-to-worker'])

  def test_fs_lz4fs_package(self):
    # generate data
    self.clear()
    os.mkdir('subdir')
    open('file1.txt', 'w').write('0123456789' * (1024 * 128))
    open(os.path.join('subdir', 'file2.txt'), 'w').write('1234567890' * (1024 * 128))
    random_data = bytearray(random.randint(0, 255) for x in range(1024 * 128 * 10 + 1))
    random_data[17] = ord('X')
    open('file3.txt', 'wb').write(random_data)

    # compress in emcc,  -s LZ4=1  tells it to tell the file packager
    print('emcc-normal')
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '2', args=['-s', 'LZ4=1', '--preload-file', 'file1.txt', '--preload-file', 'subdir/file2.txt', '--preload-file', 'file3.txt'], timeout=60)
    assert os.stat('file1.txt').st_size + os.stat(os.path.join('subdir', 'file2.txt')).st_size + os.stat('file3.txt').st_size == 3 * 1024 * 128 * 10 + 1
    assert os.stat('test.data').st_size < (3 * 1024 * 128 * 10) / 2  # over half is gone
    print('    emcc-opts')
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '2', args=['-s', 'LZ4=1', '--preload-file', 'file1.txt', '--preload-file', 'subdir/file2.txt', '--preload-file', 'file3.txt', '-O2'], timeout=60)

    # compress in the file packager, on the server. the client receives compressed data and can just use it. this is typical usage
    print('normal')
    out = subprocess.check_output([PYTHON, FILE_PACKAGER, 'files.data', '--preload', 'file1.txt', 'subdir/file2.txt', 'file3.txt', '--lz4'])
    open('files.js', 'wb').write(out)
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '2', args=['--pre-js', 'files.js', '-s', 'LZ4=1', '-s', 'FORCE_FILESYSTEM=1'], timeout=60)
    print('    opts')
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '2', args=['--pre-js', 'files.js', '-s', 'LZ4=1', '-s', 'FORCE_FILESYSTEM=1', '-O2'], timeout=60)

    # load the data into LZ4FS manually at runtime. This means we compress on the client. This is generally not recommended
    print('manual')
    subprocess.check_output([PYTHON, FILE_PACKAGER, 'files.data', '--preload', 'file1.txt', 'subdir/file2.txt', 'file3.txt', '--separate-metadata', '--js-output=files.js'])
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '1', args=['-DLOAD_MANUALLY', '-s', 'LZ4=1', '-s', 'FORCE_FILESYSTEM=1'], timeout=60)
    print('    opts')
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '1', args=['-DLOAD_MANUALLY', '-s', 'LZ4=1', '-s', 'FORCE_FILESYSTEM=1', '-O2'], timeout=60)
    print('    opts+closure')
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '1', args=['-DLOAD_MANUALLY', '-s', 'LZ4=1', '-s', 'FORCE_FILESYSTEM=1', '-O2', '--closure', '1', '-g1'], timeout=60)

    '''# non-lz4 for comparison
    try:
      os.mkdir('files')
    except:
      pass
    shutil.copyfile('file1.txt', os.path.join('files', 'file1.txt'))
    shutil.copyfile('file2.txt', os.path.join('files', 'file2.txt'))
    shutil.copyfile('file3.txt', os.path.join('files', 'file3.txt'))
    out = subprocess.check_output([PYTHON, FILE_PACKAGER, 'files.data', '--preload', 'files/file1.txt', 'files/file2.txt', 'files/file3.txt'])
    open('files.js', 'wb').write(out)
    self.btest(os.path.join('fs', 'test_lz4fs.cpp'), '2', args=['--pre-js', 'files.js'], timeout=60)'''

  def test_separate_metadata_later(self):
    # see issue #6654 - we need to handle separate-metadata both when we run before
    # the main program, and when we are run later

    open('data.dat', 'w').write(' ')
    run_process([PYTHON, FILE_PACKAGER, 'more.data', '--preload', 'data.dat', '--separate-metadata', '--js-output=more.js'])
    self.btest(os.path.join('browser', 'separate_metadata_later.cpp'), '1', args=['-s', 'FORCE_FILESYSTEM=1'])

  def test_idbstore(self):
    secret = str(time.time())
    for stage in [0, 1, 2, 3, 0, 1, 2, 0, 0, 1, 4, 2, 5]:
      self.clear()
      self.btest(path_from_root('tests', 'idbstore.c'), str(stage), force_c=True, args=['-lidbstore.js', '-DSTAGE=' + str(stage), '-DSECRET=\"' + secret + '\"'])

  def test_idbstore_sync(self):
    secret = str(time.time())
    self.clear()
    self.btest(path_from_root('tests', 'idbstore_sync.c'), '6', force_c=True, args=['-lidbstore.js', '-DSECRET=\"' + secret + '\"', '-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '--memory-init-file', '1', '-O3', '-g2'])

  def test_idbstore_sync_worker(self):
    secret = str(time.time())
    self.clear()
    self.btest(path_from_root('tests', 'idbstore_sync_worker.c'), '6', force_c=True, args=['-lidbstore.js', '-DSECRET=\"' + secret + '\"', '-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '--memory-init-file', '1', '-O3', '-g2', '--proxy-to-worker', '-s', 'TOTAL_MEMORY=80MB'])

  def test_force_exit(self):
    self.btest('force_exit.c', force_c=True, expected='17')

  def test_sdl_pumpevents(self):
    # key events should be detected using SDL_PumpEvents
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function keydown(c) {
        var event = document.createEvent("KeyboardEvent");
        event.initKeyEvent("keydown", true, true, window,
                           0, 0, 0, 0,
                           c, c);
        document.dispatchEvent(event);
      }
    ''')
    self.btest('sdl_pumpevents.c', expected='7', args=['--pre-js', 'pre.js', '-lSDL', '-lGL'])

  def test_sdl_canvas_size(self):
    self.btest('sdl_canvas_size.c', expected='1',
               args=['-O2', '--minify', '0', '--shell-file',
                     path_from_root('tests', 'sdl_canvas_size.html'), '-lSDL', '-lGL'])

  @requires_graphics_hardware
  def test_sdl_gl_read(self):
    # SDL, OpenGL, readPixels
    open(os.path.join(self.get_dir(), 'sdl_gl_read.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl_gl_read.c')).read()))
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl_gl_read.c'), '-o', 'something.html', '-lSDL', '-lGL'])
    self.run_browser('something.html', '.', '/report_result?1')

  @requires_graphics_hardware
  def test_sdl_gl_mapbuffers(self):
    self.btest('sdl_gl_mapbuffers.c', expected='1', args=['-s', 'FULL_ES3=1', '-lSDL', '-lGL'],
               message='You should see a blue triangle.')

  @requires_graphics_hardware
  def test_sdl_ogl(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_ogl.c', reference='screenshot-gray-purple.png', reference_slack=1,
               args=['-O2', '--minify', '0', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with gray at the top.')

  @requires_graphics_hardware
  def test_sdl_ogl_defaultmatrixmode(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_ogl_defaultMatrixMode.c', reference='screenshot-gray-purple.png', reference_slack=1,
               args=['--minify', '0', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with gray at the top.')

  @requires_graphics_hardware
  def test_sdl_ogl_p(self):
    # Immediate mode with pointers
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_ogl_p.c', reference='screenshot-gray.png', reference_slack=1,
               args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with gray at the top.')

  @requires_graphics_hardware
  def test_sdl_ogl_proc_alias(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_ogl_proc_alias.c', reference='screenshot-gray-purple.png', reference_slack=1,
               args=['-O2', '-g2', '-s', 'INLINING_LIMIT=1', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'])

  @requires_graphics_hardware
  def test_sdl_fog_simple(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_fog_simple.c', reference='screenshot-fog-simple.png',
               args=['-O2', '--minify', '0', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl_fog_negative(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_fog_negative.c', reference='screenshot-fog-negative.png',
               args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl_fog_density(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_fog_density.c', reference='screenshot-fog-density.png',
               args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl_fog_exp2(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_fog_exp2.c', reference='screenshot-fog-exp2.png',
               args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl_fog_linear(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_fog_linear.c', reference='screenshot-fog-linear.png', reference_slack=1,
               args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins', '-lSDL', '-lGL'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_glfw(self):
    self.btest('glfw.c', '1', args=['-s', 'LEGACY_GL_EMULATION=1', '-lglfw', '-lGL'])
    self.btest('glfw.c', '1', args=['-s', 'LEGACY_GL_EMULATION=1', '-s', 'USE_GLFW=2', '-lglfw', '-lGL'])

  def test_glfw_minimal(self):
    self.btest('glfw_minimal.c', '1', args=['-lglfw', '-lGL'])
    self.btest('glfw_minimal.c', '1', args=['-s', 'USE_GLFW=2', '-lglfw', '-lGL'])

  def test_glfw_time(self):
    self.btest('test_glfw_time.c', '1', args=['-s', 'USE_GLFW=3', '-lglfw', '-lGL'])

  @requires_graphics_hardware
  def test_egl(self):
    open(os.path.join(self.get_dir(), 'test_egl.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'test_egl.c')).read()))

    run_process([PYTHON, EMCC, '-O2', os.path.join(self.get_dir(), 'test_egl.c'), '-o', 'page.html', '-lEGL', '-lGL'])
    self.run_browser('page.html', '', '/report_result?1')

  def test_egl_width_height(self):
    open(os.path.join(self.get_dir(), 'test_egl_width_height.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'test_egl_width_height.c')).read()))

    run_process([PYTHON, EMCC, '-O2', os.path.join(self.get_dir(), 'test_egl_width_height.c'), '-o', 'page.html', '-lEGL', '-lGL'])
    self.run_browser('page.html', 'Should print "(300, 150)" -- the size of the canvas in pixels', '/report_result?1')

  def do_test_worker(self, args=[]):
    # Test running in a web worker
    open('file.dat', 'w').write('data for worker')
    html_file = open('main.html', 'w')
    html_file.write('''
      <html>
      <body>
        Worker Test
        <script>
          var worker = new Worker('worker.js');
          worker.onmessage = function(event) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'http://localhost:%s/report_result?' + event.data);
            xhr.send();
            setTimeout(function() { window.close() }, 1000);
          };
        </script>
      </body>
      </html>
    ''' % self.test_port)
    html_file.close()

    for file_data in [1, 0]:
      cmd = [PYTHON, EMCC, path_from_root('tests', 'hello_world_worker.cpp'), '-o', 'worker.js'] + (['--preload-file', 'file.dat'] if file_data else []) + args
      print(cmd)
      subprocess.check_call(cmd)
      assert os.path.exists('worker.js')
      self.run_browser('main.html', '', '/report_result?hello%20from%20worker,%20and%20|' + ('data%20for%20w' if file_data else '') + '|')

  def test_worker(self):
    self.do_test_worker()
    self.assertContained('you should not see this text when in a worker!', run_js('worker.js')) # code should run standalone too

  def test_chunked_synchronous_xhr(self):
    main = 'chunked_sync_xhr.html'
    worker_filename = "download_and_checksum_worker.js"

    html_file = open(main, 'w')
    html_file.write(r"""
      <!doctype html>
      <html>
      <head><meta charset="utf-8"><title>Chunked XHR</title></head>
      <html>
      <body>
        Chunked XHR Web Worker Test
        <script>
          var worker = new Worker(""" + json.dumps(worker_filename) + r""");
          var buffer = [];
          worker.onmessage = function(event) {
            if (event.data.channel === "stdout") {
              var xhr = new XMLHttpRequest();
              xhr.open('GET', 'http://localhost:%s/report_result?' + event.data.line);
              xhr.send();
              setTimeout(function() { window.close() }, 1000);
            } else {
              if (event.data.trace) event.data.trace.split("\n").map(function(v) { console.error(v); });
              if (event.data.line) {
                console.error(event.data.line);
              } else {
                var v = event.data.char;
                if (v == 10) {
                  var line = buffer.splice(0);
                  console.error(line = line.map(function(charCode){return String.fromCharCode(charCode);}).join(''));
                } else {
                  buffer.push(v);
                }
              }
            }
          };
        </script>
      </body>
      </html>
    """ % self.test_port)
    html_file.close()

    c_source_filename = "checksummer.c"

    prejs_filename = "worker_prejs.js"
    prejs_file = open(prejs_filename, 'w')
    prejs_file.write(r"""
      if (typeof(Module) === "undefined") Module = {};
      Module["arguments"] = ["/bigfile"];
      Module["preInit"] = function() {
          FS.createLazyFile('/', "bigfile", "http://localhost:11111/bogus_file_path", true, false);
      };
      var doTrace = true;
      Module["print"] = function(s) { self.postMessage({channel: "stdout", line: s}); };
      Module["printErr"] = function(s) { self.postMessage({channel: "stderr", char: s, trace: ((doTrace && s === 10) ? new Error().stack : null)}); doTrace = false; };
    """)
    prejs_file.close()
    # vs. os.path.join(self.get_dir(), filename)
    # vs. path_from_root('tests', 'hello_world_gles.c')
    run_process([PYTHON, EMCC, path_from_root('tests', c_source_filename), '-g', '-s', 'SMALL_XHR_CHUNKS=1', '-o', worker_filename,
                 '--pre-js', prejs_filename])
    chunkSize = 1024
    data = os.urandom(10 * chunkSize + 1) # 10 full chunks and one 1 byte chunk
    checksum = zlib.adler32(data) & 0xffffffff # Python 2 compatibility: force bigint

    server = multiprocessing.Process(target=test_chunked_synchronous_xhr_server, args=(True, chunkSize, data, checksum, self.test_port))
    server.start()
    self.run_browser(main, 'Chunked binary synchronous XHR in Web Workers!', '/report_result?' + str(checksum))
    server.terminate()
    # Avoid race condition on cleanup, wait a bit so that processes have released file locks so that test tearDown won't
    # attempt to rmdir() files in use.
    if WINDOWS:
      time.sleep(2)

  @requires_graphics_hardware
  def test_glgears(self):
    self.btest('hello_world_gles.c', reference='gears.png', reference_slack=3,
               args=['-DHAVE_BUILTIN_SINCOS', '-lGL', '-lglut'], outfile='something.html',
               message='You should see animating gears.')

  @requires_graphics_hardware
  def test_glgears_long(self):
    for proxy in [0, 1]:
      print('proxy', proxy)
      self.btest('hello_world_gles.c', expected=list(map(str, range(30, 500))), args=['-DHAVE_BUILTIN_SINCOS', '-DLONGTEST', '-lGL', '-lglut'] + (['--proxy-to-worker'] if proxy else []), timeout=30)

  @requires_graphics_hardware
  def test_glgears_animation(self):
    es2_suffix = ['', '_full', '_full_944']
    for full_es2 in [0, 1, 2]:
      print(full_es2)
      run_process([PYTHON, EMCC, path_from_root('tests', 'hello_world_gles%s.c' % es2_suffix[full_es2]), '-o', 'something.html',
                   '-DHAVE_BUILTIN_SINCOS', '-s', 'GL_TESTING=1', '-lGL', '-lglut',
                   '--shell-file', path_from_root('tests', 'hello_world_gles_shell.html')] +
                  (['-s', 'FULL_ES2=1'] if full_es2 else []))
      self.run_browser('something.html', 'You should see animating gears.', '/report_gl_result?true')

  @requires_graphics_hardware
  def test_fulles2_sdlproc(self):
    self.btest('full_es2_sdlproc.c', '1', args=['-s', 'GL_TESTING=1', '-DHAVE_BUILTIN_SINCOS', '-s', 'FULL_ES2=1', '-lGL', '-lSDL', '-lglut'])

  @requires_graphics_hardware
  def test_glgears_deriv(self):
    self.btest('hello_world_gles_deriv.c', reference='gears.png', reference_slack=2,
               args=['-DHAVE_BUILTIN_SINCOS', '-lGL', '-lglut'], outfile='something.html',
               message='You should see animating gears.')
    with open('something.html') as f:
      assert 'gl-matrix' not in f.read(), 'Should not include glMatrix when not needed'

  @requires_graphics_hardware
  def test_glbook(self):
    programs = self.get_library('glbook', [
      os.path.join('Chapter_2', 'Hello_Triangle', 'CH02_HelloTriangle.bc'),
      os.path.join('Chapter_8', 'Simple_VertexShader', 'CH08_SimpleVertexShader.bc'),
      os.path.join('Chapter_9', 'Simple_Texture2D', 'CH09_SimpleTexture2D.bc'),
      os.path.join('Chapter_9', 'Simple_TextureCubemap', 'CH09_TextureCubemap.bc'),
      os.path.join('Chapter_9', 'TextureWrap', 'CH09_TextureWrap.bc'),
      os.path.join('Chapter_10', 'MultiTexture', 'CH10_MultiTexture.bc'),
      os.path.join('Chapter_13', 'ParticleSystem', 'CH13_ParticleSystem.bc'),
    ], configure=None)

    def book_path(*pathelems):
      return path_from_root('tests', 'glbook', *pathelems)

    for program in programs:
      print(program)
      basename = os.path.basename(program)
      args = ['-lGL', '-lEGL', '-lX11']
      if basename == 'CH10_MultiTexture.bc':
        shutil.copyfile(book_path('Chapter_10', 'MultiTexture', 'basemap.tga'), os.path.join(self.get_dir(), 'basemap.tga'))
        shutil.copyfile(book_path('Chapter_10', 'MultiTexture', 'lightmap.tga'), os.path.join(self.get_dir(), 'lightmap.tga'))
        args += ['--preload-file', 'basemap.tga', '--preload-file', 'lightmap.tga']
      elif basename == 'CH13_ParticleSystem.bc':
        shutil.copyfile(book_path('Chapter_13', 'ParticleSystem', 'smoke.tga'), os.path.join(self.get_dir(), 'smoke.tga'))
        args += ['--preload-file', 'smoke.tga', '-O2'] # test optimizations and closure here as well for more coverage

      self.btest(program,
                 reference=book_path(basename.replace('.bc', '.png')),
                 args=args,
                 timeout=30)

  @requires_graphics_hardware
  def test_gles2_emulation(self):
    shutil.copyfile(path_from_root('tests', 'glbook', 'Chapter_10', 'MultiTexture', 'basemap.tga'), self.in_dir('basemap.tga'))
    shutil.copyfile(path_from_root('tests', 'glbook', 'Chapter_10', 'MultiTexture', 'lightmap.tga'), self.in_dir('lightmap.tga'))
    shutil.copyfile(path_from_root('tests', 'glbook', 'Chapter_13', 'ParticleSystem', 'smoke.tga'), self.in_dir('smoke.tga'))

    for source, reference in [
      (os.path.join('glbook', 'Chapter_2', 'Hello_Triangle', 'Hello_Triangle_orig.c'), path_from_root('tests', 'glbook', 'CH02_HelloTriangle.png')),
      # (os.path.join('glbook', 'Chapter_8', 'Simple_VertexShader', 'Simple_VertexShader_orig.c'), path_from_root('tests', 'glbook', 'CH08_SimpleVertexShader.png')), # XXX needs INT extension in WebGL
      (os.path.join('glbook', 'Chapter_9', 'TextureWrap', 'TextureWrap_orig.c'), path_from_root('tests', 'glbook', 'CH09_TextureWrap.png')),
      # (os.path.join('glbook', 'Chapter_9', 'Simple_TextureCubemap', 'Simple_TextureCubemap_orig.c'), path_from_root('tests', 'glbook', 'CH09_TextureCubemap.png')), # XXX needs INT extension in WebGL
      (os.path.join('glbook', 'Chapter_9', 'Simple_Texture2D', 'Simple_Texture2D_orig.c'), path_from_root('tests', 'glbook', 'CH09_SimpleTexture2D.png')),
      (os.path.join('glbook', 'Chapter_10', 'MultiTexture', 'MultiTexture_orig.c'), path_from_root('tests', 'glbook', 'CH10_MultiTexture.png')),
      (os.path.join('glbook', 'Chapter_13', 'ParticleSystem', 'ParticleSystem_orig.c'), path_from_root('tests', 'glbook', 'CH13_ParticleSystem.png')),
    ]:
      print(source)
      self.btest(source,
                 reference=reference,
                 args=['-I' + path_from_root('tests', 'glbook', 'Common'),
                       path_from_root('tests', 'glbook', 'Common', 'esUtil.c'),
                       path_from_root('tests', 'glbook', 'Common', 'esShader.c'),
                       path_from_root('tests', 'glbook', 'Common', 'esShapes.c'),
                       path_from_root('tests', 'glbook', 'Common', 'esTransform.c'),
                       '-s', 'FULL_ES2=1', '-lGL', '-lEGL', '-lX11',
                       '--preload-file', 'basemap.tga', '--preload-file', 'lightmap.tga', '--preload-file', 'smoke.tga'])

  @requires_graphics_hardware
  def test_clientside_vertex_arrays_es3(self):
    # NOTE: Should FULL_ES3=1 imply client-side vertex arrays? The emulation needs FULL_ES2=1 for now.
    self.btest('clientside_vertex_arrays_es3.c', reference='gl_triangle.png', args=['-s', 'USE_WEBGL2=1', '-s', 'FULL_ES2=1', '-s', 'FULL_ES3=1', '-s', 'USE_GLFW=3', '-lglfw', '-lGLESv2'])

  def test_emscripten_api(self):
    for args in [[], ['-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1']]:
      self.btest('emscripten_api_browser.cpp', '1', args=['-s', '''EXPORTED_FUNCTIONS=['_main', '_third']''', '-lSDL'])

  def test_emscripten_api2(self):
    def setup():
      open('script1.js', 'w').write('''
        Module._set(456);
      ''')
      open('file1.txt', 'w').write('first')
      open('file2.txt', 'w').write('second')

    setup()
    run_process([PYTHON, FILE_PACKAGER, 'test.data', '--preload', 'file1.txt', 'file2.txt'], stdout=open('script2.js', 'w'))
    self.btest('emscripten_api_browser2.cpp', '1', args=['-s', '''EXPORTED_FUNCTIONS=['_main', '_set']''', '-s', 'FORCE_FILESYSTEM=1'])

    # check using file packager to another dir
    self.clear()
    setup()
    os.mkdir('sub')
    run_process([PYTHON, FILE_PACKAGER, 'sub/test.data', '--preload', 'file1.txt', 'file2.txt'], stdout=open('script2.js', 'w'))
    shutil.copyfile(os.path.join('sub', 'test.data'), 'test.data')
    self.btest('emscripten_api_browser2.cpp', '1', args=['-s', '''EXPORTED_FUNCTIONS=['_main', '_set']''', '-s', 'FORCE_FILESYSTEM=1'])

  def test_emscripten_api_infloop(self):
    self.btest('emscripten_api_browser_infloop.cpp', '7')

  def test_emscripten_fs_api(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png')) # preloaded *after* run
    self.btest('emscripten_fs_api_browser.cpp', '1', args=['-lSDL'])

  def test_emscripten_fs_api2(self):
    self.btest('emscripten_fs_api_browser2.cpp', '1', args=['-s', "ASSERTIONS=0"])
    self.btest('emscripten_fs_api_browser2.cpp', '1', args=['-s', "ASSERTIONS=1"])

  def test_emscripten_main_loop(self):
    for args in [[], ['-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1', '-s', 'EXIT_RUNTIME=1']]:
      self.btest('emscripten_main_loop.cpp', '0', args=args)

  def test_emscripten_main_loop_settimeout(self):
    for args in [[], ['-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1']]:
      self.btest('emscripten_main_loop_settimeout.cpp', '1', args=args)

  def test_emscripten_main_loop_and_blocker(self):
    for args in [[], ['-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1']]:
      self.btest('emscripten_main_loop_and_blocker.cpp', '0', args=args)

  def test_emscripten_main_loop_setimmediate(self):
    for args in [[], ['--proxy-to-worker'], ['-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1']]:
      self.btest('emscripten_main_loop_setimmediate.cpp', '1', args=args)

  def test_fs_after_main(self):
    for args in [[], ['-O1']]:
      self.btest('fs_after_main.cpp', '0', args=args)

  def test_sdl_quit(self):
    self.btest('sdl_quit.c', '1', args=['-lSDL', '-lGL'])

  def test_sdl_resize(self):
    self.btest('sdl_resize.c', '1', args=['-lSDL', '-lGL'])

  def test_glshaderinfo(self):
    self.btest('glshaderinfo.cpp', '1', args=['-lGL', '-lglut'])

  @requires_graphics_hardware
  def test_glgetattachedshaders(self):
    self.btest('glgetattachedshaders.c', '1', args=['-lGL', '-lEGL'])

  # Covered by dEQP text suite (we can remove it later if we add coverage for that).
  @requires_graphics_hardware
  def test_glframebufferattachmentinfo(self):
    self.btest('glframebufferattachmentinfo.c', '1', args=['-lGLESv2', '-lEGL'])

  @requires_graphics_hardware
  def test_sdlglshader(self):
    self.btest('sdlglshader.c', reference='sdlglshader.png', args=['-O2', '--closure', '1', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_sdlglshader2(self):
    self.btest('sdlglshader2.c', expected='1', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], also_proxied=True)

  @requires_graphics_hardware
  def test_gl_glteximage(self):
    self.btest('gl_teximage.c', '1', args=['-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_gl_textures(self):
    self.btest('gl_textures.cpp', '0', args=['-lGL'])

  @requires_graphics_hardware
  def test_gl_ps(self):
    # pointers and a shader
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('gl_ps.c', reference='gl_ps.png', args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '--use-preload-plugins'], reference_slack=1)

  @requires_graphics_hardware
  def test_gl_ps_packed(self):
    # packed data that needs to be strided
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('gl_ps_packed.c', reference='gl_ps.png', args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '--use-preload-plugins'], reference_slack=1)

  @requires_graphics_hardware
  def test_gl_ps_strides(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('gl_ps_strides.c', reference='gl_ps_strides.png', args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '--use-preload-plugins'])

  @requires_graphics_hardware
  def test_gl_ps_worker(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('gl_ps_worker.c', reference='gl_ps.png', args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '--use-preload-plugins'], reference_slack=1, also_proxied=True)

  @requires_graphics_hardware
  def test_gl_renderers(self):
    self.btest('gl_renderers.c', reference='gl_renderers.png', args=['-s', 'GL_UNSAFE_OPTS=0', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_gl_stride(self):
    self.btest('gl_stride.c', reference='gl_stride.png', args=['-s', 'GL_UNSAFE_OPTS=0', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_gl_vertex_buffer_pre(self):
    self.btest('gl_vertex_buffer_pre.c', reference='gl_vertex_buffer_pre.png', args=['-s', 'GL_UNSAFE_OPTS=0', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_gl_vertex_buffer(self):
    self.btest('gl_vertex_buffer.c', reference='gl_vertex_buffer.png', args=['-s', 'GL_UNSAFE_OPTS=0', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], reference_slack=1)

  @requires_graphics_hardware
  def test_gles2_uniform_arrays(self):
    self.btest('gles2_uniform_arrays.cpp', args=['-s', 'GL_ASSERTIONS=1', '-lGL', '-lSDL'], expected=['1'], also_proxied=True)

  @requires_graphics_hardware
  def test_gles2_conformance(self):
    self.btest('gles2_conformance.cpp', args=['-s', 'GL_ASSERTIONS=1', '-lGL', '-lSDL'], expected=['1'])

  @requires_graphics_hardware
  def test_matrix_identity(self):
    self.btest('gl_matrix_identity.c', expected=['-1882984448', '460451840', '1588195328'], args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  @no_swiftshader
  def test_cubegeom_pre(self):
    self.btest('cubegeom_pre.c', reference='cubegeom_pre.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  @no_chrome("RELOCATABLE=1 forces synchronous compilation which chrome doesn't support")
  def test_cubegeom_pre_relocatable(self):
    self.btest('cubegeom_pre.c', reference='cubegeom_pre.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '-s', 'RELOCATABLE=1'])

  @requires_graphics_hardware
  @no_swiftshader
  def test_cubegeom_pre2(self):
    self.btest('cubegeom_pre2.c', reference='cubegeom_pre2.png', args=['-s', 'GL_DEBUG=1', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL']) # some coverage for GL_DEBUG not breaking the build

  @requires_graphics_hardware
  @no_swiftshader
  def test_cubegeom_pre3(self):
    self.btest('cubegeom_pre3.c', reference='cubegeom_pre2.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom(self):
    self.btest('cubegeom.c', reference='cubegeom.png', args=['-O2', '-g', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], also_proxied=True)

  @requires_graphics_hardware
  def test_cubegeom_proc(self):
    open('side.c', 'w').write(r'''

extern void* SDL_GL_GetProcAddress(const char *);

void *glBindBuffer = 0; // same name as the gl function, to check that the collision does not break us

void *getBindBuffer() {
  if (!glBindBuffer) glBindBuffer = SDL_GL_GetProcAddress("glBindBuffer");
  return glBindBuffer;
}
''')
    # also test -Os in wasm, which uses meta-dce, which should not break legacy gl emulation hacks
    for opts in [[], ['-O1'], ['-Os', '-s', 'WASM=1']]:
      self.btest('cubegeom_proc.c', reference='cubegeom.png', args=opts + ['side.c', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_glew(self):
    self.btest('cubegeom_glew.c', reference='cubegeom.png', args=['-O2', '--closure', '1', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lGLEW', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_color(self):
    self.btest('cubegeom_color.c', reference='cubegeom_color.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_normal(self):
    self.btest('cubegeom_normal.c', reference='cubegeom_normal.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], also_proxied=True)

  @requires_graphics_hardware
  def test_cubegeom_normal_dap(self): # draw is given a direct pointer to clientside memory, no element array buffer
    self.btest('cubegeom_normal_dap.c', reference='cubegeom_normal.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], also_proxied=True)

  @requires_graphics_hardware
  def test_cubegeom_normal_dap_far(self): # indices do nto start from 0
    self.btest('cubegeom_normal_dap_far.c', reference='cubegeom_normal.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_normal_dap_far_range(self): # glDrawRangeElements
    self.btest('cubegeom_normal_dap_far_range.c', reference='cubegeom_normal.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_normal_dap_far_glda(self): # use glDrawArrays
    self.btest('cubegeom_normal_dap_far_glda.c', reference='cubegeom_normal_dap_far_glda.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_normal_dap_far_glda_quad(self): # with quad
    self.btest('cubegeom_normal_dap_far_glda_quad.c', reference='cubegeom_normal_dap_far_glda_quad.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_mt(self):
    self.btest('cubegeom_mt.c', reference='cubegeom_mt.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL']) # multitexture

  @requires_graphics_hardware
  def test_cubegeom_color2(self):
    self.btest('cubegeom_color2.c', reference='cubegeom_color2.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], also_proxied=True)

  @requires_graphics_hardware
  def test_cubegeom_texturematrix(self):
    self.btest('cubegeom_texturematrix.c', reference='cubegeom_texturematrix.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_fog(self):
    self.btest('cubegeom_fog.c', reference='cubegeom_fog.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  @no_swiftshader
  def test_cubegeom_pre_vao(self):
    self.btest('cubegeom_pre_vao.c', reference='cubegeom_pre_vao.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  @no_swiftshader
  def test_cubegeom_pre2_vao(self):
    self.btest('cubegeom_pre2_vao.c', reference='cubegeom_pre_vao.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_pre2_vao2(self):
    self.btest('cubegeom_pre2_vao2.c', reference='cubegeom_pre2_vao2.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  @no_swiftshader
  def test_cubegeom_pre_vao_es(self):
    self.btest('cubegeom_pre_vao_es.c', reference='cubegeom_pre_vao.png', args=['-s', 'FULL_ES2=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_cubegeom_u4fv_2(self):
    self.btest('cubegeom_u4fv_2.c', reference='cubegeom_u4fv_2.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])
    self.btest('cubegeom_u4fv_2.c', reference='cubegeom_u4fv_2.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '-s', 'SPLIT_MEMORY=16777216', '-s', 'WASM=0']) # check for uniform4fv slice being valid in split memory

  @requires_graphics_hardware
  def test_cube_explosion(self):
    self.btest('cube_explosion.c', reference='cube_explosion.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], also_proxied=True)

  @requires_graphics_hardware
  def test_glgettexenv(self):
    self.btest('glgettexenv.c', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'], expected=['1'])

  def test_sdl_canvas_blank(self):
    self.btest('sdl_canvas_blank.c', args=['-lSDL', '-lGL'], reference='sdl_canvas_blank.png')

  def test_sdl_canvas_palette(self):
    self.btest('sdl_canvas_palette.c', args=['-lSDL', '-lGL'], reference='sdl_canvas_palette.png')

  def test_sdl_canvas_twice(self):
    self.btest('sdl_canvas_twice.c', args=['-lSDL', '-lGL'], reference='sdl_canvas_twice.png')

  def test_sdl_set_clip_rect(self):
    self.btest('sdl_set_clip_rect.c', args=['-lSDL', '-lGL'], reference='sdl_set_clip_rect.png')

  def test_sdl_maprgba(self):
    self.btest('sdl_maprgba.c', args=['-lSDL', '-lGL'], reference='sdl_maprgba.png', reference_slack=3)

  def test_sdl_create_rgb_surface_from(self):
    self.btest('sdl_create_rgb_surface_from.c', args=['-lSDL', '-lGL'], reference='sdl_create_rgb_surface_from.png')

  def test_sdl_rotozoom(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl_rotozoom.c', reference='sdl_rotozoom.png', args=['--preload-file', 'screenshot.png', '--use-preload-plugins', '-lSDL', '-lGL'], reference_slack=3)

  def test_sdl_gfx_primitives(self):
    self.btest('sdl_gfx_primitives.c', args=['-lSDL', '-lGL'], reference='sdl_gfx_primitives.png', reference_slack=1)

  def test_sdl_canvas_palette_2(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      Module['preRun'].push(function() {
        SDL.defaults.copyOnLock = false;
      });
    ''')

    open(os.path.join(self.get_dir(), 'args-r.js'), 'w').write('''
      Module['arguments'] = ['-r'];
    ''')

    open(os.path.join(self.get_dir(), 'args-g.js'), 'w').write('''
      Module['arguments'] = ['-g'];
    ''')

    open(os.path.join(self.get_dir(), 'args-b.js'), 'w').write('''
      Module['arguments'] = ['-b'];
    ''')

    self.btest('sdl_canvas_palette_2.c', reference='sdl_canvas_palette_r.png', args=['--pre-js', 'pre.js', '--pre-js', 'args-r.js', '-lSDL', '-lGL'])
    self.btest('sdl_canvas_palette_2.c', reference='sdl_canvas_palette_g.png', args=['--pre-js', 'pre.js', '--pre-js', 'args-g.js', '-lSDL', '-lGL'])
    self.btest('sdl_canvas_palette_2.c', reference='sdl_canvas_palette_b.png', args=['--pre-js', 'pre.js', '--pre-js', 'args-b.js', '-lSDL', '-lGL'])

  def test_sdl_ttf_render_text_solid(self):
    self.btest('sdl_ttf_render_text_solid.c', reference='sdl_ttf_render_text_solid.png', args=['-O2', '-s', 'TOTAL_MEMORY=16MB', '-lSDL', '-lGL'])

  def test_sdl_alloctext(self):
    self.btest('sdl_alloctext.c', expected='1', args=['-O2', '-s', 'TOTAL_MEMORY=16MB', '-lSDL', '-lGL'])

  def test_sdl_surface_refcount(self):
    self.btest('sdl_surface_refcount.c', args=['-lSDL'], expected='1')

  def test_sdl_free_screen(self):
    self.btest('sdl_free_screen.cpp', args=['-lSDL', '-lGL'], reference='htmltest.png')

  @requires_graphics_hardware
  def test_glbegin_points(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('glbegin_points.c', reference='glbegin_points.png', args=['--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '--use-preload-plugins'])

  @requires_graphics_hardware
  def test_s3tc(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.dds'), os.path.join(self.get_dir(), 'screenshot.dds'))
    self.btest('s3tc.c', reference='s3tc.png', args=['--preload-file', 'screenshot.dds', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_s3tc_ffp_only(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.dds'), os.path.join(self.get_dir(), 'screenshot.dds'))
    self.btest('s3tc.c', reference='s3tc.png', args=['--preload-file', 'screenshot.dds', '-s', 'LEGACY_GL_EMULATION=1', '-s', 'GL_FFP_ONLY=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_aniso(self):
    if SPIDERMONKEY_ENGINE in JS_ENGINES:
      # asm.js-ification check
      run_process([PYTHON, EMCC, path_from_root('tests', 'aniso.c'), '-O2', '-g2', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '-Wno-incompatible-pointer-types'])
      self.set_setting('ASM_JS', 1)
      self.run_generated_code(SPIDERMONKEY_ENGINE, 'a.out.js', assert_returncode=None)
      print('passed asm test')

    shutil.copyfile(path_from_root('tests', 'water.dds'), 'water.dds')
    self.btest('aniso.c', reference='aniso.png', reference_slack=2, args=['--preload-file', 'water.dds', '-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL', '-Wno-incompatible-pointer-types'])

  @requires_graphics_hardware
  def test_tex_nonbyte(self):
    self.btest('tex_nonbyte.c', reference='tex_nonbyte.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_float_tex(self):
    self.btest('float_tex.cpp', reference='float_tex.png', args=['-lGL', '-lglut'])

  @requires_graphics_hardware
  def test_subdata(self):
    self.btest('gl_subdata.cpp', reference='float_tex.png', args=['-lGL', '-lglut'])

  @requires_graphics_hardware
  def test_perspective(self):
    self.btest('perspective.c', reference='perspective.png', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL', '-lSDL'])

  @requires_graphics_hardware
  def test_glerror(self):
    self.btest('gl_error.c', expected='1', args=['-s', 'LEGACY_GL_EMULATION=1', '-lGL'])

  def test_openal_error(self):
    for args in [[], ['--closure', '1']]:
      print(args)
      self.btest('openal_error.c', expected='1', args=args)

  def test_openal_capture_sanity(self):
    self.btest('openal_capture_sanity.c', expected='0')

  def test_runtimelink(self):
    for wasm in [0, 1]:
      print(wasm)
      main, supp = self.setup_runtimelink_test()
      open('supp.cpp', 'w').write(supp)
      run_process([PYTHON, EMCC, 'supp.cpp', '-o', 'supp.' + ('wasm' if wasm else 'js'), '-s', 'SIDE_MODULE=1', '-O2', '-s', 'WASM=%d' % wasm])
      self.btest(main, args=['-DBROWSER=1', '-s', 'MAIN_MODULE=1', '-O2', '-s', 'WASM=%d' % wasm, '-s', 'RUNTIME_LINKED_LIBS=["supp.' + ('wasm' if wasm else 'js') + '"]'], expected='76')

  def test_pre_run_deps(self):
    # Adding a dependency in preRun will delay run
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      Module.preRun = function() {
        addRunDependency();
        out('preRun called, added a dependency...');
        setTimeout(function() {
          Module.okk = 10;
          removeRunDependency()
        }, 2000);
      };
    ''')

    for mem in [0, 1]:
      self.btest('pre_run_deps.cpp', expected='10', args=['--pre-js', 'pre.js', '--memory-init-file', str(mem)])

  def test_mem_init(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function myJSCallback() { // called from main()
        Module._note(1);
      }
      Module.preRun = function() {
        addOnPreMain(function() {
          Module._note(2);
        });
      };
    ''')
    open(os.path.join(self.get_dir(), 'post.js'), 'w').write('''
      var assert = function(check, text) {
        if (!check) {
          var xhr = new XMLHttpRequest();
          xhr.open('GET', 'http://localhost:%s/report_result?9');
          xhr.onload = function() {
            window.close();
          };
          xhr.send();
        }
      }
      Module._note(4); // this happens too early! and is overwritten when the mem init arrives
    ''' % self.test_port)

    # with assertions, we notice when memory was written to too early
    self.btest('mem_init.cpp', expected='9', args=['-s', 'WASM=0', '--pre-js', 'pre.js', '--post-js', 'post.js', '--memory-init-file', '1'])
    # otherwise, we just overwrite
    self.btest('mem_init.cpp', expected='3', args=['-s', 'WASM=0', '--pre-js', 'pre.js', '--post-js', 'post.js', '--memory-init-file', '1', '-s', 'ASSERTIONS=0'])

  def test_mem_init_request(self):
    def test(what, status):
      print(what, status)
      open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
        var xhr = Module.memoryInitializerRequest = new XMLHttpRequest();
        xhr.open('GET', "''' + what + '''", true);
        xhr.responseType = 'arraybuffer';
        xhr.send(null);

        console.warn = function(x) {
          if (x.indexOf('a problem seems to have happened with Module.memoryInitializerRequest') >= 0) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'http://localhost:%s/report_result?0');
            setTimeout(xhr.onload = function() {
              console.log('close!');
              window.close();
            }, 1000);
            xhr.send();
            throw 'halt';
          }
          console.log('WARNING: ' + x);
        };
      ''' % self.test_port)
      self.btest('mem_init_request.cpp', expected=status, args=['-s', 'WASM=0', '--pre-js', 'pre.js', '--memory-init-file', '1'])

    test('test.html.mem', '1')
    test('nothing.nowhere', '0')

  def test_runtime_misuse(self):
    post_prep = '''
      var expected_ok = false;
      function doCcall(n) {
        ccall('note', 'string', ['number'], [n]);
      }
      var wrapped = cwrap('note', 'string', ['number']); // returns a string to suppress cwrap optimization
      function doCwrapCall(n) {
        var str = wrapped(n);
        out('got ' + str);
        assert(str === 'silly-string');
      }
      function doDirectCall(n) {
        Module['_note'](n);
      }
    '''
    post_test = '''
      var ok = false;
      try {
        doCcall(1);
        ok = true; // should fail and not reach here, runtime is not ready yet so ccall will abort
      } catch(e) {
        out('expected fail 1');
        assert(e.toString().indexOf('assert') >= 0); // assertion, not something else
        ABORT = false; // hackish
      }
      assert(ok === expected_ok);

      ok = false;
      try {
        doCwrapCall(2);
        ok = true; // should fail and not reach here, runtime is not ready yet so cwrap call will abort
      } catch(e) {
        out('expected fail 2');
        assert(e.toString().indexOf('assert') >= 0); // assertion, not something else
        ABORT = false; // hackish
      }
      assert(ok === expected_ok);

      ok = false;
      try {
        doDirectCall(3);
        ok = true; // should fail and not reach here, runtime is not ready yet so any code execution
      } catch(e) {
        out('expected fail 3');
        assert(e.toString().indexOf('assert') >= 0); // assertion, not something else
        ABORT = false; // hackish
      }
      assert(ok === expected_ok);
    '''

    post_hook = r'''
      function myJSCallback() {
        // called from main, this is an ok time
        doCcall(100);
        doCwrapCall(200);
        doDirectCall(300);
      }

      setTimeout(function() {
        var xhr = new XMLHttpRequest();
        assert(Module.noted);
        xhr.open('GET', 'http://localhost:%s/report_result?' + HEAP32[Module.noted>>2]);
        xhr.send();
        setTimeout(function() { window.close() }, 1000);
      }, 1000);
    ''' % self.test_port

    open('pre_runtime.js', 'w').write(r'''
      Module.onRuntimeInitialized = function(){
        myJSCallback();
      };
    ''')

    for filename, extra_args, second_code in [
      ('runtime_misuse.cpp', [], 600),
      ('runtime_misuse_2.cpp', ['--pre-js', 'pre_runtime.js'], 601) # 601, because no main means we *do* run another call after exit()
    ]:
      for mode in [[], ['-s', 'WASM=1']]:
        print('\n', filename, extra_args, mode)
        print('mem init, so async, call too early')
        open(os.path.join(self.get_dir(), 'post.js'), 'w').write(post_prep + post_test + post_hook)
        self.btest(filename, expected='600', args=['--post-js', 'post.js', '--memory-init-file', '1', '-s', 'EXIT_RUNTIME=1'] + extra_args + mode)
        print('sync startup, call too late')
        open(os.path.join(self.get_dir(), 'post.js'), 'w').write(post_prep + 'Module.postRun.push(function() { ' + post_test + ' });' + post_hook)
        self.btest(filename, expected=str(second_code), args=['--post-js', 'post.js', '--memory-init-file', '0', '-s', 'EXIT_RUNTIME=1'] + extra_args + mode)
        print('sync, runtime still alive, so all good')
        open(os.path.join(self.get_dir(), 'post.js'), 'w').write(post_prep + 'expected_ok = true; Module.postRun.push(function() { ' + post_test + ' });' + post_hook)
        self.btest(filename, expected='606', args=['--post-js', 'post.js', '--memory-init-file', '0'] + extra_args + mode)

  def test_cwrap_early(self):
    self.btest(os.path.join('browser', 'cwrap_early.cpp'), args=['-O2', '-s', 'ASSERTIONS=1', '--pre-js', path_from_root('tests', 'browser', 'cwrap_early.js'), '-s', 'EXTRA_EXPORTED_RUNTIME_METHODS=["cwrap"]'], expected='0')

  def test_worker_api(self):
    run_process([PYTHON, EMCC, path_from_root('tests', 'worker_api_worker.cpp'), '-o', 'worker.js', '-s', 'BUILD_AS_WORKER=1', '-s', 'EXPORTED_FUNCTIONS=["_one"]'])
    self.btest('worker_api_main.cpp', expected='566')

  def test_worker_api_2(self):
    run_process([PYTHON, EMCC, path_from_root('tests', 'worker_api_2_worker.cpp'), '-o', 'worker.js', '-s', 'BUILD_AS_WORKER=1', '-O2', '--minify', '0', '-s', 'EXPORTED_FUNCTIONS=["_one", "_two", "_three", "_four"]', '--closure', '1'])
    self.btest('worker_api_2_main.cpp', args=['-O2', '--minify', '0'], expected='11')

  def test_worker_api_3(self):
    run_process([PYTHON, EMCC, path_from_root('tests', 'worker_api_3_worker.cpp'), '-o', 'worker.js', '-s', 'BUILD_AS_WORKER=1', '-s', 'EXPORTED_FUNCTIONS=["_one"]'])
    self.btest('worker_api_3_main.cpp', expected='5')

  def test_worker_api_sleep(self):
    run_process([PYTHON, EMCC, path_from_root('tests', 'worker_api_worker_sleep.cpp'), '-o', 'worker.js', '-s', 'BUILD_AS_WORKER=1', '-s', 'EXPORTED_FUNCTIONS=["_one"]', '-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1'])
    self.btest('worker_api_main.cpp', expected='566')

  def test_emscripten_async_wget2(self):
    self.btest('http.cpp', expected='0', args=['-I' + path_from_root('tests')])

  # TODO: test only worked in non-fastcomp
  @unittest.skip('non-fastcomp is deprecated and fails in 3.5')
  def test_module(self):
    run_process([PYTHON, EMCC, path_from_root('tests', 'browser_module.cpp'), '-o', 'module.js', '-O2', '-s', 'SIDE_MODULE=1', '-s', 'DLOPEN_SUPPORT=1', '-s', 'EXPORTED_FUNCTIONS=["_one", "_two"]'])
    self.btest('browser_main.cpp', args=['-O2', '-s', 'MAIN_MODULE=1', '-s', 'DLOPEN_SUPPORT=1'], expected='8')

  def test_preload_module(self):
    open('library.c', 'w').write(r'''
      #include <stdio.h>
      int library_func() {
        return 42;
      }
    ''')
    run_process([PYTHON, EMCC, 'library.c', '-s', 'SIDE_MODULE=1', '-O2', '-o', 'library.wasm', '-s', 'WASM=1'])
    os.rename('library.wasm', 'library.so')
    main = r'''
      #include <dlfcn.h>
      #include <stdio.h>
      #include <emscripten.h>
      int main() {
        int found = EM_ASM_INT(
          return Module['preloadedWasm']['/library.so'] !== undefined;
        );
        if (!found) {
          REPORT_RESULT(1);
          return 1;
        }
        void *lib_handle = dlopen("/library.so", 0);
        if (!lib_handle) {
          REPORT_RESULT(2);
          return 2;
        }
        typedef int (*voidfunc)();
        voidfunc x = (voidfunc)dlsym(lib_handle, "library_func");
        if (!x || x() != 42) {
          REPORT_RESULT(3);
          return 3;
        }
        REPORT_RESULT(0);
        return 0;
      }
    '''
    self.btest(
      main,
      args=['-s', 'MAIN_MODULE=1', '--preload-file', '.@/', '-O2', '-s', 'WASM=1', '--use-preload-plugins'],
      expected='0')

  def test_mmap_file(self):
    open(self.in_dir('data.dat'), 'w').write('data from the file ' + ('.' * 9000))
    for extra_args in [[], ['--no-heap-copy']]:
      self.btest(path_from_root('tests', 'mmap_file.c'), expected='1', args=['--preload-file', 'data.dat'] + extra_args)

  def test_emrun_info(self):
    if not has_browser():
      self.skipTest('need a browser')
    result = run_process([PYTHON, path_from_root('emrun'), '--system_info', '--browser_info'], stdout=PIPE).stdout
    assert 'CPU' in result
    assert 'Browser' in result
    assert 'Traceback' not in result

    result = run_process([PYTHON, path_from_root('emrun'), '--list_browsers'], stdout=PIPE).stdout
    assert 'Traceback' not in result

  # Deliberately named as test_zzz_emrun to make this test the last one
  # as this test may take the focus away from the main test window
  # by opening a new window and possibly not closing it.
  def test_zzz_emrun(self):
    run_process([PYTHON, EMCC, path_from_root('tests', 'test_emrun.c'), '--emrun', '-o', 'hello_world.html'])
    outdir = os.getcwd()
    if not has_browser():
      self.skipTest('need a browser')
    # We cannot run emrun from the temp directory the suite will clean up afterwards, since the browser that is launched will have that directory as startup directory,
    # and the browser will not close as part of the test, pinning down the cwd on Windows and it wouldn't be possible to delete it. Therefore switch away from that directory
    # before launching.
    os.chdir(path_from_root())
    args = [PYTHON, path_from_root('emrun'), '--timeout', '30', '--safe_firefox_profile', '--port', '6939', '--verbose', '--log_stdout', os.path.join(outdir, 'stdout.txt'), '--log_stderr', os.path.join(outdir, 'stderr.txt')]
    if EMTEST_BROWSER is not None:
      # If EMTEST_BROWSER carried command line arguments to pass to the browser,
      # (e.g. "firefox -profile /path/to/foo") those can't be passed via emrun,
      # so strip them out.
      browser_cmd = shlex.split(EMTEST_BROWSER)
      browser_path = browser_cmd[0]
      args += ['--browser', browser_path]
      if len(browser_cmd) > 1:
        browser_args = browser_cmd[1:]
        if 'firefox' in browser_path and '-profile' in browser_args:
          # emrun uses its own -profile, strip it out
          parser = argparse.ArgumentParser(add_help=False) # otherwise it throws with -headless
          parser.add_argument('-profile')
          browser_args = parser.parse_known_args(browser_args)[1]
        if browser_args:
          args += ['--browser_args', ' ' + ' '.join(browser_args)]
    args += [os.path.join(outdir, 'hello_world.html'), '1', '2', '--3']
    proc = run_process(args, check=False)
    stdout = open(os.path.join(outdir, 'stdout.txt'), 'r').read()
    stderr = open(os.path.join(outdir, 'stderr.txt'), 'r').read()
    assert proc.returncode == 100
    assert 'argc: 4' in stdout
    assert 'argv[3]: --3' in stdout
    assert 'hello, world!' in stdout
    assert 'Testing ASCII characters: !"$%&\'()*+,-./:;<=>?@[\\]^_`{|}~' in stdout
    assert 'Testing char sequences: %20%21 &auml;' in stdout
    assert 'hello, error stream!' in stderr

  # This does not actually verify anything except that --cpuprofiler and --memoryprofiler compiles.
  # Run interactive.test_cpuprofiler_memoryprofiler for interactive testing.
  @requires_graphics_hardware
  def test_cpuprofiler_memoryprofiler(self):
    self.btest('hello_world_gles.c', expected='0', args=['-DLONGTEST=1', '-DTEST_MEMORYPROFILER_ALLOCATIONS_MAP=1', '-O2', '--cpuprofiler', '--memoryprofiler', '-lGL', '-lglut'], timeout=30)

  def test_uuid(self):
    # Run with ./runner.py browser.test_uuid
    # We run this test in Node/SPIDERMONKEY and browser environments because we try to make use of
    # high quality crypto random number generators such as crypto.getRandomValues or randomBytes (if available).

    # First run tests in Node and/or SPIDERMONKEY using run_js. Use closure compiler so we can check that
    # require('crypto').randomBytes and window.crypto.getRandomValues doesn't get minified out.
    run_process([PYTHON, EMCC, '-O2', '--closure', '1', path_from_root('tests', 'uuid', 'test.c'), '-o', 'test.js', '-luuid'], stdout=PIPE, stderr=PIPE)

    test_js_closure = open('test.js').read()

    # Check that test.js compiled with --closure 1 contains ").randomBytes" and "window.crypto.getRandomValues"
    assert ").randomBytes" in test_js_closure
    assert "window.crypto.getRandomValues" in test_js_closure

    out = run_js('test.js', full_output=True)
    print(out)

    # Tidy up files that might have been created by this test.
    try_delete(path_from_root('tests', 'uuid', 'test.js'))
    try_delete(path_from_root('tests', 'uuid', 'test.js.map'))

    # Now run test in browser
    self.btest(path_from_root('tests', 'uuid', 'test.c'), '1', args=['-luuid'])

  @requires_graphics_hardware
  def test_glew(self):
    self.btest(path_from_root('tests', 'glew.c'), args=['-lGL', '-lSDL', '-lGLEW'], expected='1')
    self.btest(path_from_root('tests', 'glew.c'), args=['-lGL', '-lSDL', '-lGLEW', '-s', 'LEGACY_GL_EMULATION=1'], expected='1')
    self.btest(path_from_root('tests', 'glew.c'), args=['-lGL', '-lSDL', '-lGLEW', '-DGLEW_MX'], expected='1')
    self.btest(path_from_root('tests', 'glew.c'), args=['-lGL', '-lSDL', '-lGLEW', '-s', 'LEGACY_GL_EMULATION=1', '-DGLEW_MX'], expected='1')

  def test_doublestart_bug(self):
    open('pre.js', 'w').write(r'''
if (!Module['preRun']) Module['preRun'] = [];
Module["preRun"].push(function () {
  addRunDependency('test_run_dependency');
  removeRunDependency('test_run_dependency');
});
''')

    self.btest('doublestart.c', args=['--pre-js', 'pre.js', '-o', 'test.html'], expected='1')

  def test_html5(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1']]:
      print(opts)
      self.btest(path_from_root('tests', 'test_html5.c'), args=opts, expected='0', timeout=20)

  @requires_graphics_hardware
  def test_html5_webgl_create_context_no_antialias(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1'], ['-s', 'FULL_ES2=1']]:
      print(opts)
      self.btest(path_from_root('tests', 'webgl_create_context.cpp'), args=opts + ['-DNO_ANTIALIAS', '-lGL'], expected='0', timeout=20)

  # This test supersedes the one above, but it's skipped in the CI because anti-aliasing is not well supported by the Mesa software renderer.
  @requires_graphics_hardware
  def test_html5_webgl_create_context(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1'], ['-s', 'FULL_ES2=1']]:
      print(opts)
      self.btest(path_from_root('tests', 'webgl_create_context.cpp'), args=opts + ['-lGL'], expected='0', timeout=20)

  @requires_graphics_hardware
  # Verify bug https://github.com/kripken/emscripten/issues/4556: creating a WebGL context to Module.canvas without an ID explicitly assigned to it.
  def test_html5_webgl_create_context2(self):
    self.btest(path_from_root('tests', 'webgl_create_context2.cpp'), args=['--shell-file', path_from_root('tests', 'webgl_create_context2_shell.html'), '-lGL'], expected='0', timeout=20)

  @requires_graphics_hardware
  def test_html5_webgl_destroy_context(self):
    for opts in [[], ['-O2', '-g1'], ['-s', 'FULL_ES2=1']]:
      print(opts)
      self.btest(path_from_root('tests', 'webgl_destroy_context.cpp'), args=opts + ['--shell-file', path_from_root('tests/webgl_destroy_context_shell.html'), '-lGL'], expected='0', timeout=20)

  @requires_graphics_hardware
  def test_webgl_context_params(self):
    if WINDOWS:
      self.skipTest('SKIPPED due to bug https://bugzilla.mozilla.org/show_bug.cgi?id=1310005 - WebGL implementation advertises implementation defined GL_IMPLEMENTATION_COLOR_READ_TYPE/FORMAT pair that it cannot read with')
    self.btest(path_from_root('tests', 'webgl_color_buffer_readpixels.cpp'), args=['-lGL'], expected='0', timeout=20)

  # Test for PR#5373 (https://github.com/kripken/emscripten/pull/5373)
  def test_webgl_shader_source_length(self):
    for opts in [[], ['-s', 'FULL_ES2=1']]:
      print(opts)
      self.btest(path_from_root('tests', 'webgl_shader_source_length.cpp'), args=opts + ['-lGL'], expected='0', timeout=20)

  def test_webgl2(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1'], ['-s', 'FULL_ES2=1']]:
      print(opts)
      self.btest(path_from_root('tests', 'webgl2.cpp'), args=['-s', 'USE_WEBGL2=1', '-lGL'] + opts, expected='0')

  def test_webgl2_objects(self):
    self.btest(path_from_root('tests', 'webgl2_objects.cpp'), args=['-s', 'USE_WEBGL2=1', '-lGL'], expected='0')

  def test_webgl2_ubos(self):
    self.btest(path_from_root('tests', 'webgl2_ubos.cpp'), args=['-s', 'USE_WEBGL2=1', '-lGL'], expected='0')

  @requires_graphics_hardware
  def test_webgl2_garbage_free_entrypoints(self):
    self.btest(path_from_root('tests', 'webgl2_garbage_free_entrypoints.cpp'), args=['-s', 'USE_WEBGL2=1', '-DTEST_WEBGL2=1'], expected='1')
    self.btest(path_from_root('tests', 'webgl2_garbage_free_entrypoints.cpp'), expected='1')

  @requires_graphics_hardware
  def test_webgl2_backwards_compatibility_emulation(self):
    self.btest(path_from_root('tests', 'webgl2_backwards_compatibility_emulation.cpp'), args=['-s', 'USE_WEBGL2=1', '-s', 'WEBGL2_BACKWARDS_COMPATIBILITY_EMULATION=1'], expected='0')

  @requires_graphics_hardware
  def test_webgl_with_closure(self):
    self.btest(path_from_root('tests', 'webgl_with_closure.cpp'), args=['-O2', '-s', 'USE_WEBGL2=1', '--closure', '1', '-lGL'], expected='0')

  def test_sdl_touch(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1']]:
      print(opts)
      self.btest(path_from_root('tests', 'sdl_touch.c'), args=opts + ['-DAUTOMATE_SUCCESS=1', '-lSDL', '-lGL'], expected='0')

  def test_html5_mouse(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1']]:
      print(opts)
      self.btest(path_from_root('tests', 'test_html5_mouse.c'), args=opts + ['-DAUTOMATE_SUCCESS=1'], expected='0')

  def test_sdl_mousewheel(self):
    for opts in [[], ['-O2', '-g1', '--closure', '1']]:
      print(opts)
      self.btest(path_from_root('tests', 'test_sdl_mousewheel.c'), args=opts + ['-DAUTOMATE_SUCCESS=1', '-lSDL', '-lGL'], expected='0')

  def test_codemods(self):
    # tests asm.js client-side code modifications
    for opt_level in [0, 2]:
      print('opt level', opt_level)
      opts = ['-O' + str(opt_level), '-s', 'WASM=0']
      # sanity checks, building with and without precise float semantics generates different results
      self.btest(path_from_root('tests', 'codemods.cpp'), expected='2', args=opts)
      self.btest(path_from_root('tests', 'codemods.cpp'), expected='1', args=opts + ['-s', 'PRECISE_F32=1'])
      self.btest(path_from_root('tests', 'codemods.cpp'), expected='1', args=opts + ['-s', 'PRECISE_F32=2', '--separate-asm']) # empty polyfill, but browser has support, so semantics are like float

  def test_wget(self):
    with open(os.path.join(self.get_dir(), 'test.txt'), 'w') as f:
      f.write('emscripten')
    self.btest(path_from_root('tests', 'test_wget.c'), expected='1', args=['-s', 'ASYNCIFY=1'])
    print('asyncify+emterpreter')
    self.btest(path_from_root('tests', 'test_wget.c'), expected='1', args=['-s', 'ASYNCIFY=1', '-s', 'EMTERPRETIFY=1'])
    print('emterpreter by itself')
    self.btest(path_from_root('tests', 'test_wget.c'), expected='1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1'])

  def test_wget_data(self):
    with open(os.path.join(self.get_dir(), 'test.txt'), 'w') as f:
      f.write('emscripten')
    self.btest(path_from_root('tests', 'test_wget_data.c'), expected='1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O2', '-g2'])
    self.btest(path_from_root('tests', 'test_wget_data.c'), expected='1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O2', '-g2', '-s', 'ASSERTIONS=1'])

  def test_locate_file(self):
    for wasm in [0, 1]:
      print('wasm', wasm)
      self.clear()
      open('src.cpp', 'w').write(self.with_report_result(r'''
        #include <stdio.h>
        #include <string.h>
        #include <assert.h>
        int main() {
          FILE *f = fopen("data.txt", "r");
          assert(f && "could not open file");
          char buf[100];
          int num = fread(buf, 1, 20, f);
          assert(num == 20 && "could not read 20 bytes");
          buf[20] = 0;
          fclose(f);
          int result = !strcmp("load me right before", buf);
          printf("|%s| : %d\n", buf, result);
          REPORT_RESULT(result);
          return 0;
        }
      '''))
      open('data.txt', 'w').write('load me right before...')
      open('pre.js', 'w').write('Module.locateFile = function(x) { return "sub/" + x };')
      run_process([PYTHON, FILE_PACKAGER, 'test.data', '--preload', 'data.txt'], stdout=open('data.js', 'w'))
      # put pre.js first, then the file packager data, so locateFile is there for the file loading code
      run_process([PYTHON, EMCC, 'src.cpp', '-O2', '-g', '--pre-js', 'pre.js', '--pre-js', 'data.js', '-o', 'page.html', '-s', 'FORCE_FILESYSTEM=1', '-s', 'WASM=' + str(wasm)])
      os.mkdir('sub')
      if wasm:
        shutil.move('page.wasm', os.path.join('sub', 'page.wasm'))
      else:
        shutil.move('page.html.mem', os.path.join('sub', 'page.html.mem'))
      shutil.move('test.data', os.path.join('sub', 'test.data'))
      self.run_browser('page.html', None, '/report_result?1')

      # alternatively, put locateFile in the HTML
      print('in html')

      open('shell.html', 'w').write('''
        <body>
          <script>
            var Module = {
              locateFile: function(x) { return "sub/" + x }
            };
          </script>

          {{{ SCRIPT }}}
        </body>
      ''')

      def in_html(expected, args=[]):
        run_process([PYTHON, EMCC, 'src.cpp', '-O2', '-g', '--shell-file', 'shell.html', '--pre-js', 'data.js', '-o', 'page.html', '-s', 'SAFE_HEAP=1', '-s', 'ASSERTIONS=1', '-s', 'FORCE_FILESYSTEM=1', '-s', 'WASM=' + str(wasm)] + args)
        if wasm:
          shutil.move('page.wasm', os.path.join('sub', 'page.wasm'))
        else:
          shutil.move('page.html.mem', os.path.join('sub', 'page.html.mem'))
        self.run_browser('page.html', None, '/report_result?' + expected)

      in_html('1')

      # verify that the mem init request succeeded in the latter case
      if not wasm:
        open('src.cpp', 'w').write(self.with_report_result(r'''
  #include <stdio.h>
  #include <emscripten.h>

  int main() {
    int result = EM_ASM_INT({
      return Module['memoryInitializerRequest'].status;
    });
    printf("memory init request: %d\n", result);
    REPORT_RESULT(result);
    return 0;
  }
      '''))

        in_html('200')

  @requires_graphics_hardware
  def test_glfw3(self):
    for opts in [[], ['-Os', '--closure', '1']]:
      print(opts)
      self.btest(path_from_root('tests', 'glfw3.c'), args=['-s', 'LEGACY_GL_EMULATION=1', '-s', 'USE_GLFW=3', '-lglfw', '-lGL'] + opts, expected='1')

  @requires_graphics_hardware
  def test_glfw_events(self):
    self.btest(path_from_root('tests', 'glfw_events.c'), args=['-s', 'USE_GLFW=2', "-DUSE_GLFW=2", '-lglfw', '-lGL'], expected='1')
    self.btest(path_from_root('tests', 'glfw_events.c'), args=['-s', 'USE_GLFW=3', "-DUSE_GLFW=3", '-lglfw', '-lGL'], expected='1')

  def test_asm_swapping(self):
    self.clear()
    open('run.js', 'w').write(r'''
Module['onRuntimeInitialized'] = function() {
  // test proper initial result
  var result = Module._func();
  console.log('first: ' + result);
  if (result !== 10) throw 'bad first result';

  // load second module to be swapped in
  var second = document.createElement('script');
  second.onload = function() { console.log('loaded second') };
  second.src = 'second.js';
  document.body.appendChild(second);
  console.log('second appended');

  Module['onAsmSwap'] = function() {
    console.log('swapped');
    // verify swapped-in result
    var result = Module._func();
    console.log('second: ' + result);
    if (result !== 22) throw 'bad second result';
    Module._report(999);
    console.log('reported');
  };
};
''')
    for opts in [[], ['-O1'], ['-O2', '-profiling'], ['-O2']]:
      print(opts)
      opts += ['-s', 'WASM=0', '--pre-js', 'run.js', '-s', 'SWAPPABLE_ASM_MODULE=1'] # important that both modules are built with the same opts
      open('second.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'asm_swap2.cpp')).read()))
      run_process([PYTHON, EMCC, 'second.cpp'] + opts)
      run_process([PYTHON, path_from_root('tools', 'distill_asm.py'), 'a.out.js', 'second.js', 'swap-in'])
      assert os.path.exists('second.js')

      if isinstance(SPIDERMONKEY_ENGINE, list) and len(SPIDERMONKEY_ENGINE[0]) != 0:
        out = run_js('second.js', engine=SPIDERMONKEY_ENGINE, stderr=PIPE, full_output=True, assert_returncode=None)
        self.validate_asmjs(out)
      else:
        print('Skipping asm validation check, spidermonkey is not configured')

      self.btest(path_from_root('tests', 'asm_swap.cpp'), args=opts, expected='999')

  def test_sdl2_image(self):
    # load an image file, get pixel data. Also O2 coverage for --preload-file, and memory-init
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.jpg'))
    open(os.path.join(self.get_dir(), 'sdl2_image.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_image.c')).read()))

    for mem in [0, 1]:
      for dest, dirname, basename in [('screenshot.jpg', '/', 'screenshot.jpg'),
                                      ('screenshot.jpg@/assets/screenshot.jpg', '/assets', 'screenshot.jpg')]:
        run_process([
          PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_image.c'), '-o', 'page.html', '-O2', '--memory-init-file', str(mem),
          '--preload-file', dest, '-DSCREENSHOT_DIRNAME="' + dirname + '"', '-DSCREENSHOT_BASENAME="' + basename + '"', '-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '--use-preload-plugins'
        ])
        self.run_browser('page.html', '', '/report_result?600')

  def test_sdl2_image_jpeg(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.jpeg'))
    open(os.path.join(self.get_dir(), 'sdl2_image_jpeg.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_image.c')).read()))
    run_process([
      PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_image_jpeg.c'), '-o', 'page.html',
      '--preload-file', 'screenshot.jpeg', '-DSCREENSHOT_DIRNAME="/"', '-DSCREENSHOT_BASENAME="screenshot.jpeg"', '-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '--use-preload-plugins'
    ])
    self.run_browser('page.html', '', '/report_result?600')

  def test_sdl2_image_formats(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl2_image.c', expected='512', args=['--preload-file', 'screenshot.png', '-DSCREENSHOT_DIRNAME="/"', '-DSCREENSHOT_BASENAME="screenshot.png"',
                                                     '-DNO_PRELOADED', '-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '-s', 'SDL2_IMAGE_FORMATS=["png"]'])

  def test_sdl2_key(self):
    for defines in [[]]:
      open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
        Module.postRun = function() {
          function doOne() {
            Module._one();
            setTimeout(doOne, 1000/60);
          }
          setTimeout(doOne, 1000/60);
        }

        function keydown(c) {
          var event = document.createEvent("KeyboardEvent");
          event.initKeyEvent("keydown", true, true, window,
                             0, 0, 0, 0,
                             c, c);
          var prevented = !document.dispatchEvent(event);

          //send keypress if not prevented
          if (!prevented) {
            event = document.createEvent("KeyboardEvent");
            event.initKeyEvent("keypress", true, true, window,
                               0, 0, 0, 0, 0, c);
            document.dispatchEvent(event);
          }
        }

        function keyup(c) {
          var event = document.createEvent("KeyboardEvent");
          event.initKeyEvent("keyup", true, true, window,
                             0, 0, 0, 0,
                             c, c);
          document.dispatchEvent(event);
        }
      ''')
      open(os.path.join(self.get_dir(), 'sdl2_key.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_key.c')).read()))

      run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_key.c'), '-o', 'page.html'] + defines + ['-s', 'USE_SDL=2', '--pre-js', 'pre.js', '-s', '''EXPORTED_FUNCTIONS=['_main', '_one']'''])
      self.run_browser('page.html', '', '/report_result?37182145')

  def test_sdl2_text(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      Module.postRun = function() {
        function doOne() {
          Module._one();
          setTimeout(doOne, 1000/60);
        }
        setTimeout(doOne, 1000/60);
      }

      function simulateKeyEvent(charCode) {
        var event = document.createEvent("KeyboardEvent");
        event.initKeyEvent("keypress", true, true, window,
                           0, 0, 0, 0, 0, charCode);
        document.body.dispatchEvent(event);
      }
    ''')
    open(os.path.join(self.get_dir(), 'sdl2_text.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_text.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_text.c'), '-o', 'page.html', '--pre-js', 'pre.js', '-s', '''EXPORTED_FUNCTIONS=['_main', '_one']''', '-s', 'USE_SDL=2'])
    self.run_browser('page.html', '', '/report_result?1')

  def test_sdl2_mouse(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function simulateMouseEvent(x, y, button) {
        var event = document.createEvent("MouseEvents");
        if (button >= 0) {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousedown', true, true, window,
                     1, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event1);
          var event2 = document.createEvent("MouseEvents");
          event2.initMouseEvent('mouseup', true, true, window,
                     1, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event2);
        } else {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousemove', true, true, window,
                     0, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y, Module['canvas'].offsetLeft + x, Module['canvas'].offsetTop + y,
                     0, 0, 0, 0,
                     0, null);
          Module['canvas'].dispatchEvent(event1);
        }
      }
      window['simulateMouseEvent'] = simulateMouseEvent;
    ''')
    open(os.path.join(self.get_dir(), 'sdl2_mouse.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_mouse.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_mouse.c'), '-O2', '--minify', '0', '-o', 'page.html', '--pre-js', 'pre.js', '-s', 'USE_SDL=2'])
    self.run_browser('page.html', '', '/report_result?1', timeout=30)

  def test_sdl2_mouse_offsets(self):
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function simulateMouseEvent(x, y, button) {
        var event = document.createEvent("MouseEvents");
        if (button >= 0) {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousedown', true, true, window,
                     1, x, y, x, y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event1);
          var event2 = document.createEvent("MouseEvents");
          event2.initMouseEvent('mouseup', true, true, window,
                     1, x, y, x, y,
                     0, 0, 0, 0,
                     button, null);
          Module['canvas'].dispatchEvent(event2);
        } else {
          var event1 = document.createEvent("MouseEvents");
          event1.initMouseEvent('mousemove', true, true, window,
                     0, x, y, x, y,
                     0, 0, 0, 0,
                     0, null);
          Module['canvas'].dispatchEvent(event1);
        }
      }
      window['simulateMouseEvent'] = simulateMouseEvent;
    ''')
    open(os.path.join(self.get_dir(), 'page.html'), 'w').write('''
      <html>
        <head>
          <style type="text/css">
            html, body { margin: 0; padding: 0; }
            #container {
              position: absolute;
              left: 5px; right: 0;
              top: 5px; bottom: 0;
            }
            #canvas {
              position: absolute;
              left: 0; width: 600px;
              top: 0; height: 450px;
            }
            textarea {
              margin-top: 500px;
              margin-left: 5px;
              width: 600px;
            }
          </style>
        </head>
        <body>
          <div id="container">
            <canvas id="canvas"></canvas>
          </div>
          <textarea id="output" rows="8"></textarea>
          <script type="text/javascript">
            var Module = {
              canvas: document.getElementById('canvas'),
              print: (function() {
                var element = document.getElementById('output');
                element.value = ''; // clear browser cache
                return function(text) {
                  if (arguments.length > 1) text = Array.prototype.slice.call(arguments).join(' ');
                  element.value += text + "\\n";
                  element.scrollTop = element.scrollHeight; // focus on bottom
                };
              })()
            };
          </script>
          <script type="text/javascript" src="sdl2_mouse.js"></script>
        </body>
      </html>
    ''')
    open(os.path.join(self.get_dir(), 'sdl2_mouse.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_mouse.c')).read()))

    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_mouse.c'), '-DTEST_SDL_MOUSE_OFFSETS=1', '-O2', '--minify', '0', '-o', 'sdl2_mouse.js', '--pre-js', 'pre.js', '-s', 'USE_SDL=2'])
    self.run_browser('page.html', '', '/report_result?1')

  @requires_graphics_hardware
  def test_sdl2glshader(self):
    self.btest('sdl2glshader.c', reference='sdlglshader.png', args=['-s', 'USE_SDL=2', '-O2', '--closure', '1', '-s', 'LEGACY_GL_EMULATION=1'])
    self.btest('sdl2glshader.c', reference='sdlglshader.png', args=['-s', 'USE_SDL=2', '-O2', '-s', 'LEGACY_GL_EMULATION=1'], also_proxied=True) # XXX closure fails on proxy

  def test_sdl2_canvas_blank(self):
    self.btest('sdl2_canvas_blank.c', reference='sdl_canvas_blank.png', args=['-s', 'USE_SDL=2'])

  def test_sdl2_canvas_palette(self):
    self.btest('sdl2_canvas_palette.c', reference='sdl_canvas_palette.png', args=['-s', 'USE_SDL=2'])

  def test_sdl2_canvas_twice(self):
    self.btest('sdl2_canvas_twice.c', reference='sdl_canvas_twice.png', args=['-s', 'USE_SDL=2'])

  def zzztest_sdl2_gfx_primitives(self):
    self.btest('sdl2_gfx_primitives.c', args=['-s', 'USE_SDL=2', '-lSDL2_gfx'], reference='sdl_gfx_primitives.png', reference_slack=1)

  def test_sdl2_canvas_palette_2(self):
    open(os.path.join(self.get_dir(), 'args-r.js'), 'w').write('''
      Module['arguments'] = ['-r'];
    ''')

    open(os.path.join(self.get_dir(), 'args-g.js'), 'w').write('''
      Module['arguments'] = ['-g'];
    ''')

    open(os.path.join(self.get_dir(), 'args-b.js'), 'w').write('''
      Module['arguments'] = ['-b'];
    ''')

    self.btest('sdl2_canvas_palette_2.c', reference='sdl_canvas_palette_r.png', args=['-s', 'USE_SDL=2', '--pre-js', 'args-r.js'])
    self.btest('sdl2_canvas_palette_2.c', reference='sdl_canvas_palette_g.png', args=['-s', 'USE_SDL=2', '--pre-js', 'args-g.js'])
    self.btest('sdl2_canvas_palette_2.c', reference='sdl_canvas_palette_b.png', args=['-s', 'USE_SDL=2', '--pre-js', 'args-b.js'])

  def test_sdl2_swsurface(self):
    self.btest('sdl2_swsurface.c', expected='1', args=['-s', 'USE_SDL=2'])

  def test_sdl2_image_prepare(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl2_image_prepare.c', reference='screenshot.jpg', args=['--preload-file', 'screenshot.not', '-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2'])

  def test_sdl2_image_prepare_data(self):
    # load an image file, get pixel data.
    shutil.copyfile(path_from_root('tests', 'screenshot.jpg'), os.path.join(self.get_dir(), 'screenshot.not'))
    self.btest('sdl2_image_prepare_data.c', reference='screenshot.jpg', args=['--preload-file', 'screenshot.not', '-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2'])

  @requires_graphics_hardware
  def test_sdl2_canvas_proxy(self):
    def post():
      html = open('test.html').read()
      html = html.replace('</body>', '''
<script>
function assert(x, y) { if (!x) throw 'assertion failed ' + y }

%s

var windowClose = window.close;
window.close = function() {
  // wait for rafs to arrive and the screen to update before reftesting
  setTimeout(function() {
    doReftest();
    setTimeout(windowClose, 5000);
  }, 1000);
};
</script>
</body>''' % open('reftest.js').read())
      open('test.html', 'w').write(html)

    open('data.txt', 'w').write('datum')

    self.btest('sdl2_canvas_proxy.c', reference='sdl2_canvas.png', args=['-s', 'USE_SDL=2', '--proxy-to-worker', '--preload-file', 'data.txt', '-s', 'GL_TESTING=1'], manual_reference=True, post_build=post)

  def test_sdl2_pumpevents(self):
    # key events should be detected using SDL_PumpEvents
    open(os.path.join(self.get_dir(), 'pre.js'), 'w').write('''
      function keydown(c) {
        var event = document.createEvent("KeyboardEvent");
        event.initKeyEvent("keydown", true, true, window,
                           0, 0, 0, 0,
                           c, c);
        document.dispatchEvent(event);
      }
    ''')
    self.btest('sdl2_pumpevents.c', expected='7', args=['--pre-js', 'pre.js', '-s', 'USE_SDL=2'])

  def test_sdl2_timer(self):
    self.btest('sdl2_timer.c', expected='5', args=['-s', 'USE_SDL=2'])

  def test_sdl2_canvas_size(self):
    self.btest('sdl2_canvas_size.c', expected='1', args=['-s', 'USE_SDL=2'])

  @requires_graphics_hardware
  def test_sdl2_gl_read(self):
    # SDL, OpenGL, readPixels
    open(os.path.join(self.get_dir(), 'sdl2_gl_read.c'), 'w').write(self.with_report_result(open(path_from_root('tests', 'sdl2_gl_read.c')).read()))
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'sdl2_gl_read.c'), '-o', 'something.html', '-s', 'USE_SDL=2'])
    self.run_browser('something.html', '.', '/report_result?1')

  @requires_graphics_hardware
  def test_sdl2_fog_simple(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl2_fog_simple.c', reference='screenshot-fog-simple.png',
               args=['-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '-O2', '--minify', '0', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl2_fog_negative(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl2_fog_negative.c', reference='screenshot-fog-negative.png',
               args=['-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl2_fog_density(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl2_fog_density.c', reference='screenshot-fog-density.png',
               args=['-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl2_fog_exp2(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl2_fog_exp2.c', reference='screenshot-fog-exp2.png',
               args=['-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins'],
               message='You should see an image with fog.')

  @requires_graphics_hardware
  def test_sdl2_fog_linear(self):
    shutil.copyfile(path_from_root('tests', 'screenshot.png'), os.path.join(self.get_dir(), 'screenshot.png'))
    self.btest('sdl2_fog_linear.c', reference='screenshot-fog-linear.png', reference_slack=1,
               args=['-s', 'USE_SDL=2', '-s', 'USE_SDL_IMAGE=2', '--preload-file', 'screenshot.png', '-s', 'LEGACY_GL_EMULATION=1', '--use-preload-plugins'],
               message='You should see an image with fog.')

  def test_sdl2_unwasteful(self):
    self.btest('sdl2_unwasteful.cpp', expected='1', args=['-s', 'USE_SDL=2', '-O1'])

  def test_sdl2_canvas_write(self):
    self.btest('sdl2_canvas_write.cpp', expected='0', args=['-s', 'USE_SDL=2'])

  @requires_graphics_hardware
  def test_sdl2_gl_frames_swap(self):
    def post_build(*args):
      self.post_manual_reftest(*args)
      html = open('test.html').read()
      html2 = html.replace('''Module['postRun'] = doReftest;''', '') # we don't want the very first frame
      assert html != html2
      open('test.html', 'w').write(html2)
    self.btest('sdl2_gl_frames_swap.c', reference='sdl2_gl_frames_swap.png', args=['--proxy-to-worker', '-s', 'GL_TESTING=1', '-s', 'USE_SDL=2'], manual_reference=True, post_build=post_build)

  @requires_graphics_hardware
  def test_sdl2_ttf(self):
    shutil.copy2(path_from_root('tests', 'freetype', 'LiberationSansBold.ttf'), self.get_dir())
    self.btest('sdl2_ttf.c', reference='sdl2_ttf.png',
               args=['-O2', '-s', 'USE_SDL=2', '-s', 'USE_SDL_TTF=2', '--embed-file', 'LiberationSansBold.ttf'],
               message='You should see colorful "hello" and "world" in the window',
               timeout=30)

  def test_sdl2_custom_cursor(self):
    shutil.copyfile(path_from_root('tests', 'cursor.bmp'), os.path.join(self.get_dir(), 'cursor.bmp'))
    self.btest('sdl2_custom_cursor.c', expected='1', args=['--preload-file', 'cursor.bmp', '-s', 'USE_SDL=2'])

  def test_sdl2_misc(self):
    self.btest('sdl2_misc.c', expected='1', args=['-s', 'USE_SDL=2'])
    print('also test building to object files first')
    src = open(path_from_root('tests', 'sdl2_misc.c')).read()
    open('test.c', 'w').write(self.with_report_result(src))
    run_process([PYTHON, EMCC, 'test.c', '-s', 'USE_SDL=2', '-o', 'test.o'])
    run_process([PYTHON, EMCC, 'test.o', '-s', 'USE_SDL=2', '-o', 'test.html'])
    self.run_browser('test.html', '...', '/report_result?1')

  @requires_graphics_hardware
  def test_cocos2d_hello(self):
    cocos2d_root = os.path.join(system_libs.Ports.get_build_dir(), 'Cocos2d')
    preload_file = os.path.join(cocos2d_root, 'samples', 'HelloCpp', 'Resources') + '@'
    self.btest('cocos2d_hello.cpp', reference='cocos2d_hello.png', reference_slack=1,
               args=['-s', 'USE_COCOS2D=3', '-s', 'ERROR_ON_UNDEFINED_SYMBOLS=0', '--std=c++11', '--preload-file', preload_file, '--use-preload-plugins'],
               message='You should see Cocos2d logo',
               timeout=30)

  def test_emterpreter_async(self):
    for opts in [0, 1, 2, 3]:
      print(opts)
      self.btest('emterpreter_async.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts), '-g2'])

  def test_emterpreter_async_2(self):
    # Error.stackTraceLimit default to 10 in chrome but this test relies on more
    # than 40 stack frames being reported.
    with open('pre.js', 'w') as f:
      f.write('Error.stackTraceLimit = 80;\n')
    self.btest('emterpreter_async_2.cpp', '40', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O3', '--pre-js', 'pre.js', ])

  def test_emterpreter_async_virtual(self):
    for opts in [0, 1, 2, 3]:
      print(opts)
      self.btest('emterpreter_async_virtual.cpp', '5', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts), '-profiling'])

  def test_emterpreter_async_virtual_2(self):
    for opts in [0, 1, 2, 3]:
      print(opts)
      self.btest('emterpreter_async_virtual_2.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts), '-s', 'ASSERTIONS=1', '-s', 'SAFE_HEAP=1', '-profiling'])

  def test_emterpreter_async_bad(self):
    for opts in [0, 1, 2, 3]:
      print(opts)
      self.btest('emterpreter_async_bad.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts), '-s', 'EMTERPRETIFY_BLACKLIST=["_middle"]', '-s', 'ASSERTIONS=1'])

  def test_emterpreter_async_bad_2(self):
    for opts in [0, 1, 2, 3]:
      for assertions in [0, 1]:
        # without assertions, we end up continuing to run more non-emterpreted code in this testcase, returning 1
        # with assertions, we hit the emterpreter-async assertion on that, and report a  clear error
        expected = '2' if assertions else '1'
        print(opts, assertions, expected)
        self.btest('emterpreter_async_bad_2.cpp', expected, args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts), '-s', 'EMTERPRETIFY_BLACKLIST=["_middle"]', '-s', 'ASSERTIONS=%s' % assertions])

  def test_emterpreter_async_mainloop(self):
    for opts in [0, 1, 2, 3]:
      print(opts)
      self.btest('emterpreter_async_mainloop.cpp', '121', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts)], timeout=20)

  def test_emterpreter_async_with_manual(self):
    for opts in [0, 1, 2, 3]:
      print(opts)
      self.btest('emterpreter_async_with_manual.cpp', '121', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-O' + str(opts), '-s', 'EMTERPRETIFY_BLACKLIST=["_acall"]'], timeout=20)

  def test_emterpreter_async_sleep2(self):
    self.btest('emterpreter_async_sleep2.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-Oz'])

  def test_emterpreter_async_sleep2_safeheap(self):
    # check that safe-heap machinery does not cause errors in async operations
    self.btest('emterpreter_async_sleep2_safeheap.cpp', '17', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-Oz', '-profiling', '-s', 'SAFE_HEAP=1', '-s', 'ASSERTIONS=1', '-s', 'EMTERPRETIFY_WHITELIST=["_main","_callback","_fix"]', '-s', 'EXIT_RUNTIME=1'])

  @requires_sound_hardware
  def test_sdl_audio_beep_sleep(self):
    self.btest('sdl_audio_beep_sleep.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-Os', '-s', 'ASSERTIONS=1', '-s', 'DISABLE_EXCEPTION_CATCHING=0', '-profiling', '-s', 'SAFE_HEAP=1', '-lSDL'], timeout=90)

  def test_mainloop_reschedule(self):
    self.btest('mainloop_reschedule.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1', '-Os'], timeout=30)

  def test_mainloop_infloop(self):
    self.btest('mainloop_infloop.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1'], timeout=30)

  def test_emterpreter_async_iostream(self):
    self.btest('emterpreter_async_iostream.cpp', '1', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_ASYNC=1'])

  def test_modularize(self):
    for opts in [[], ['-O1'], ['-O2', '-profiling'], ['-O2'], ['-O2', '--closure', '1']]:
      for args, code in [
        ([], 'Module();'), # defaults
        # use EXPORT_NAME
        (['-s', 'EXPORT_NAME="HelloWorld"'], '''
          if (typeof Module !== "undefined") throw "what?!"; // do not pollute the global scope, we are modularized!
          HelloWorld.noInitialRun = true; // errorneous module capture will load this and cause timeout
          HelloWorld();
        '''),
        # pass in a Module option (which prevents main(), which we then invoke ourselves)
        (['-s', 'EXPORT_NAME="HelloWorld"'], '''
          var hello = HelloWorld({ noInitialRun: true, onRuntimeInitialized: function() {
            setTimeout(function() { hello._main(); }); // must be async, because onRuntimeInitialized may be called synchronously, so |hello| is not yet set!
          } });
        '''),
        # similar, but without a mem init file, everything is sync and simple
        (['-s', 'EXPORT_NAME="HelloWorld"', '--memory-init-file', '0'], '''
          var hello = HelloWorld({ noInitialRun: true});
          hello._main();
        '''),
        # use the then() API
        (['-s', 'EXPORT_NAME="HelloWorld"'], '''
          HelloWorld({ noInitialRun: true }).then(function(hello) {
            hello._main();
          });
        '''),
        # then() API, also note the returned value
        (['-s', 'EXPORT_NAME="HelloWorld"'], '''
          var helloOutside = HelloWorld({ noInitialRun: true }).then(function(hello) {
            setTimeout(function() {
              hello._main();
              if (hello !== helloOutside) throw 'helloOutside has not been set!'; // as we are async, helloOutside must have been set
            });
          });
        '''),
      ]:
        print('test on', opts, args, code)
        src = open(path_from_root('tests', 'browser_test_hello_world.c')).read()
        open('test.c', 'w').write(self.with_report_result(src))
        # this test is synchronous, so avoid async startup due to wasm features
        run_process([PYTHON, EMCC, 'test.c', '-s', 'MODULARIZE=1', '-s', 'BINARYEN_ASYNC_COMPILATION=0', '-s', 'SINGLE_FILE=1'] + args + opts)
        open('a.html', 'w').write('''
          <script src="a.out.js"></script>
          <script>
            %s
          </script>
        ''' % code)
        self.run_browser('a.html', '...', '/report_result?0')

  # test illustrating the regression on the modularize feature since commit c5af8f6
  # when compiling with the --preload-file option
  def test_modularize_and_preload_files(self):
    # amount of memory different from the default one that will be allocated for the emscripten heap
    totalMemory = 33554432
    for opts in [[], ['-O1'], ['-O2', '-profiling'], ['-O2'], ['-O2', '--closure', '1']]:
      # the main function simply checks that the amount of allocated heap memory is correct
      src = r'''
        #include <stdio.h>
        #include <emscripten.h>
        int main() {
          EM_ASM({
            // use eval here in order for the test with closure compiler enabled to succeed
            var totalMemory = Module['TOTAL_MEMORY'];
            assert(totalMemory === %d, 'bad memory size');
          });
          REPORT_RESULT(0);
          return 0;
        }
      ''' % totalMemory
      open('test.c', 'w').write(self.with_report_result(src))
      # generate a dummy file
      open('dummy_file', 'w').write('dummy')
      # compile the code with the modularize feature and the preload-file option enabled
      # no wasm, since this tests customizing total memory at runtime
      run_process([PYTHON, EMCC, 'test.c', '-s', 'WASM=0', '-s', 'MODULARIZE=1', '-s', 'EXPORT_NAME="Foo"', '--preload-file', 'dummy_file'] + opts)
      open('a.html', 'w').write('''
        <script src="a.out.js"></script>
        <script>
          // instantiate the Foo module with custom TOTAL_MEMORY value
          var foo = Foo({ TOTAL_MEMORY: %d });
        </script>
      ''' % totalMemory)
      self.run_browser('a.html', '...', '/report_result?0')

  def test_webidl(self):
    # see original in test_core.py
    run_process([PYTHON, path_from_root('tools', 'webidl_binder.py'),
                 path_from_root('tests', 'webidl', 'test.idl'),
                 'glue'])
    assert os.path.exists('glue.cpp')
    assert os.path.exists('glue.js')
    for opts in [[], ['-O1'], ['-O2']]:
      print(opts)
      self.btest(os.path.join('webidl', 'test.cpp'), '1', args=['--post-js', 'glue.js', '-I.', '-DBROWSER'] + opts)

  @no_chrome("required synchronous wasm compilation")
  def test_dynamic_link(self):
    open('pre.js', 'w').write('''
      Module.dynamicLibraries = ['side.wasm'];
  ''')
    open('main.cpp', 'w').write(r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <string.h>
      #include <emscripten.h>
      char *side(const char *data);
      int main() {
        char *temp = side("hello through side\n");
        char *ret = (char*)malloc(strlen(temp)+1);
        strcpy(ret, temp);
        temp[1] = 'x';
        EM_ASM({
          Module.realPrint = out;
          out = function(x) {
            if (!Module.printed) Module.printed = x;
            Module.realPrint(x);
          };
        });
        puts(ret);
        EM_ASM({ assert(Module.printed === 'hello through side', ['expected', Module.printed]); });
        REPORT_RESULT(2);
        return 0;
      }
    ''')
    open('side.cpp', 'w').write(r'''
      #include <stdlib.h>
      #include <string.h>
      char *side(const char *data);
      char *side(const char *data) {
        char *ret = (char*)malloc(strlen(data)+1);
        strcpy(ret, data);
        return ret;
      }
    ''')
    run_process([PYTHON, EMCC, 'side.cpp', '-s', 'SIDE_MODULE=1', '-O2', '-o', 'side.wasm'])
    self.btest(self.in_dir('main.cpp'), '2', args=['-s', 'MAIN_MODULE=1', '-O2', '--pre-js', 'pre.js'])

    print('wasm in worker (we can read binary data synchronously there)')

    open('pre.js', 'w').write('''
      var Module = { dynamicLibraries: ['side.wasm'] };
  ''')
    run_process([PYTHON, EMCC, 'side.cpp', '-s', 'SIDE_MODULE=1', '-O2', '-o', 'side.wasm', '-s', 'WASM=1'])
    self.btest(self.in_dir('main.cpp'), '2', args=['-s', 'MAIN_MODULE=1', '-O2', '--pre-js', 'pre.js', '-s', 'WASM=1', '--proxy-to-worker'])

    print('wasm (will auto-preload since no sync binary reading)')

    open('pre.js', 'w').write('''
      Module.dynamicLibraries = ['side.wasm'];
  ''')
    # same wasm side module works
    self.btest(self.in_dir('main.cpp'), '2', args=['-s', 'MAIN_MODULE=1', '-O2', '--pre-js', 'pre.js', '-s', 'WASM=1'])

  @requires_graphics_hardware
  @no_chrome("required synchronous wasm compilation")
  def test_dynamic_link_glemu(self):
    open('pre.js', 'w').write('''
      Module.dynamicLibraries = ['side.wasm'];
  ''')
    open('main.cpp', 'w').write(r'''
      #include <stdio.h>
      #include <string.h>
      #include <assert.h>
      const char *side();
      int main() {
        const char *exts = side();
        puts(side());
        assert(strstr(exts, "GL_EXT_texture_env_combine"));
        REPORT_RESULT(1);
        return 0;
      }
    ''')
    open('side.cpp', 'w').write(r'''
      #include "SDL/SDL.h"
      #include "SDL/SDL_opengl.h"
      const char *side() {
        SDL_Init(SDL_INIT_VIDEO);
        SDL_SetVideoMode(600, 600, 16, SDL_OPENGL);
        return (const char *)glGetString(GL_EXTENSIONS);
      }
    ''')
    run_process([PYTHON, EMCC, 'side.cpp', '-s', 'SIDE_MODULE=1', '-O2', '-o', 'side.wasm', '-lSDL'])

    self.btest(self.in_dir('main.cpp'), '1', args=['-s', 'MAIN_MODULE=1', '-O2', '-s', 'LEGACY_GL_EMULATION=1', '-lSDL', '-lGL', '--pre-js', 'pre.js'])

  def test_memory_growth_during_startup(self):
    open('data.dat', 'w').write('X' * (30 * 1024 * 1024))
    self.btest('browser_test_hello_world.c', '0', args=['-s', 'ASSERTIONS=1', '-s', 'ALLOW_MEMORY_GROWTH=1', '-s', 'TOTAL_MEMORY=16MB', '-s', 'TOTAL_STACK=5000', '--preload-file', 'data.dat'])

  # pthreads tests

  def prep_no_SAB(self):
    open('html.html', 'w').write(open(path_from_root('src', 'shell_minimal.html')).read().replace('''<body>''', '''<body>
      <script>
        SharedArrayBuffer = undefined;
        Atomics = undefined;
      </script>
    '''))

  # Test that the emscripten_ atomics api functions work.
  def test_pthread_atomics(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_atomics.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test 64-bit atomics.
  def test_pthread_64bit_atomics(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_64bit_atomics.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test 64-bit C++11 atomics.
  def test_pthread_64bit_cxx11_atomics(self):
    for opt in [['-O0'], ['-O3']]:
      for pthreads in [[], ['-s', 'USE_PTHREADS=1']]:
        self.btest(path_from_root('tests', 'pthread', 'test_pthread_64bit_cxx11_atomics.cpp'), expected='0', args=opt + pthreads + ['-std=c++11'])

  # Test the old GCC atomic __sync_fetch_and_op builtin operations.
  def test_pthread_gcc_atomic_fetch_and_op(self):
    # We need to resort to using regexes to optimize out SharedArrayBuffer when pthreads are not supported, which is brittle!
    # Therefore perform very extensive testing of different codegen modes to catch any problems.
    for opt in [[], ['-O1'], ['-O2'], ['-O3'], ['-O3', '-s', 'AGGRESSIVE_VARIABLE_ELIMINATION=1'], ['-Os'], ['-Oz']]:
      for debug in [[], ['-g1'], ['-g2'], ['-g4']]:
        for f32 in [[], ['-s', 'PRECISE_F32=1', '--separate-asm', '-s', 'WASM=0']]:
          print(opt, debug, f32)
          self.btest(path_from_root('tests', 'pthread', 'test_pthread_gcc_atomic_fetch_and_op.cpp'), expected='0', args=opt + debug + f32 + ['-s', 'TOTAL_MEMORY=64MB', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # 64 bit version of the above test.
  def test_pthread_gcc_64bit_atomic_fetch_and_op(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_gcc_64bit_atomic_fetch_and_op.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'], also_asmjs=True)

  # Test the old GCC atomic __sync_op_and_fetch builtin operations.
  def test_pthread_gcc_atomic_op_and_fetch(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_gcc_atomic_op_and_fetch.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'], also_asmjs=True)

  # 64 bit version of the above test.
  def test_pthread_gcc_64bit_atomic_op_and_fetch(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_gcc_64bit_atomic_op_and_fetch.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'], also_asmjs=True)

  # Tests the rest of the remaining GCC atomics after the two above tests.
  def test_pthread_gcc_atomics(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_gcc_atomics.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test the __sync_lock_test_and_set and __sync_lock_release primitives.
  def test_pthread_gcc_spinlock(self):
    for arg in [[], ['-DUSE_EMSCRIPTEN_INTRINSICS']]:
      self.btest(path_from_root('tests', 'pthread', 'test_pthread_gcc_spinlock.cpp'), expected='800', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'] + arg, also_asmjs=True)

  # Test that basic thread creation works.
  def test_pthread_create(self):
    for opt in [['-O0'], ['-O3']]:
      print(str(opt))
      self.btest(path_from_root('tests', 'pthread', 'test_pthread_create.cpp'), expected='0', args=opt + ['-s', 'TOTAL_MEMORY=64MB', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Tests the -s PROXY_TO_PTHREAD=1 option.
  def test_pthread_proxy_to_pthread(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_proxy_to_pthread.c'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1'], timeout=30)

  # Test that a pthread can spawn another pthread of its own.
  def test_pthread_create_pthread(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_create_pthread.cpp'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=2'])

  # Test another case of pthreads spawning pthreads, but this time the callers immediately join on the threads they created.
  def test_pthread_nested_spawns(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_nested_spawns.cpp'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=2'])

  # Test that main thread can wait for a pthread to finish via pthread_join().
  def test_pthread_join(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_join.cpp'), expected='6765', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test pthread_cancel() operation
  def test_pthread_cancel(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_cancel.cpp'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test pthread_kill() operation
  @no_chrome('pthread_kill hangs chrome renderer, and keep subsequent tests from passing')
  def test_pthread_kill(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_kill.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test that pthread cleanup stack (pthread_cleanup_push/_pop) works.
  def test_pthread_cleanup(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_cleanup.cpp'), expected='907640832', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Tests the pthread mutex api.
  def test_pthread_mutex(self):
    for arg in [[], ['-DSPINLOCK_TEST']]:
      self.btest(path_from_root('tests', 'pthread', 'test_pthread_mutex.cpp'), expected='50', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'] + arg)

  # Test that memory allocation is thread-safe.
  def test_pthread_malloc(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_malloc.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Stress test pthreads allocating memory that will call to sbrk(), and main thread has to free up the data.
  def test_pthread_malloc_free(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_malloc_free.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8', '-s', 'TOTAL_MEMORY=256MB'])

  # Test that the pthread_barrier API works ok.
  def test_pthread_barrier(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_barrier.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test the pthread_once() function.
  def test_pthread_once(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_once.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test against a certain thread exit time handling bug by spawning tons of threads.
  def test_pthread_spawns(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_spawns.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # It is common for code to flip volatile global vars for thread control. This is a bit lax, but nevertheless, test whether that
  # kind of scheme will work with Emscripten as well.
  def test_pthread_volatile(self):
    for arg in [[], ['-DUSE_C_VOLATILE']]:
      self.btest(path_from_root('tests', 'pthread', 'test_pthread_volatile.cpp'), expected='1', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'] + arg)

  # Test thread-specific data (TLS).
  def test_pthread_thread_local_storage(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_thread_local_storage.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test the pthread condition variable creation and waiting.
  def test_pthread_condition_variable(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_condition_variable.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8'])

  # Test that pthreads are able to do printf.
  def test_pthread_printf(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_printf.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test that pthreads are able to do cout. Failed due to https://bugzilla.mozilla.org/show_bug.cgi?id=1154858.
  def test_pthread_iostream(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_iostream.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test that the main thread is able to use pthread_set/getspecific.
  def test_pthread_setspecific_mainthread(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_setspecific_mainthread.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1'], also_asmjs=True)

  # Test the -s PTHREAD_HINT_NUM_CORES=x command line variable.
  def test_pthread_num_logical_cores(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_num_logical_cores.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_HINT_NUM_CORES=2'], also_asmjs=True)

  # Test that pthreads have access to filesystem.
  def test_pthread_file_io(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_file_io.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test that the pthread_create() function operates benignly in the case that threading is not supported.
  def test_pthread_supported(self):
    for args in [[], ['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8']]:
      self.btest(path_from_root('tests', 'pthread', 'test_pthread_supported.cpp'), expected='0', args=['-O3'] + args)

  def test_pthread_separate_asm_pthreads(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_atomics.cpp'), expected='0', args=['-s', 'TOTAL_MEMORY=64MB', '-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8', '--separate-asm', '--profiling'])

  def test_pthread_custom_pthread_main_url(self):
    self.clear()
    os.makedirs(os.path.join(self.get_dir(), 'cdn'))
    open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write(self.with_report_result(r'''
      #include <stdio.h>
      #include <string.h>
      #include <emscripten/emscripten.h>
      #include <emscripten/threading.h>
      #include <pthread.h>
      int result = 0;
      void *thread_main(void *arg) {
        emscripten_atomic_store_u32(&result, 1);
        pthread_exit(0);
      }

      int main() {
        pthread_t t;
        if (emscripten_has_threading_support()) {
          pthread_create(&t, 0, thread_main, 0);
          pthread_join(t, 0);
        } else {
          result = 1;
        }
        REPORT_RESULT(result);
      }
    '''))

    # Test that it is possible to define "Module.locateFile" string to locate where pthread-main.js will be loaded from.
    open(self.in_dir('shell.html'), 'w').write(open(path_from_root('src', 'shell.html')).read().replace('var Module = {', 'var Module = { locateFile: function (path, prefix) {if (path.endsWith(".wasm")) {return prefix + path;} else {return "cdn/" + path;}}, '))
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'shell.html', '-s', 'WASM=0', '-s', 'IN_TEST_HARNESS=1', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1', '-o', 'test.html'])
    shutil.move('pthread-main.js', os.path.join('cdn', 'pthread-main.js'))
    self.run_browser('test.html', '', '/report_result?1')

    # Test that it is possible to define "Module.locateFile(foo)" function to locate where pthread-main.js will be loaded from.
    open(self.in_dir('shell2.html'), 'w').write(open(path_from_root('src', 'shell.html')).read().replace('var Module = {', 'var Module = { locateFile: function(filename) { if (filename == "pthread-main.js") return "cdn/pthread-main.js"; else return filename; }, '))
    run_process([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'shell2.html', '-s', 'WASM=0', '-s', 'IN_TEST_HARNESS=1', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1', '-o', 'test2.html'])
    try_delete('pthread-main.js')
    self.run_browser('test2.html', '', '/report_result?1')

  # Test that if the main thread is performing a futex wait while a pthread needs it to do a proxied operation (before that pthread would wake up the main thread), that it's not a deadlock.
  def test_pthread_proxying_in_futex_wait(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_proxying_in_futex_wait.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test that sbrk() operates properly in multithreaded conditions
  def test_pthread_sbrk(self):
    for aborting_malloc in [0, 1]:
      print('aborting malloc=' + str(aborting_malloc))
      # With aborting malloc = 1, test allocating memory in threads
      # With aborting malloc = 0, allocate so much memory in threads that some of the allocations fail.
      self.btest(path_from_root('tests', 'pthread', 'test_pthread_sbrk.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=8', '--separate-asm', '-s', 'ABORTING_MALLOC=' + str(aborting_malloc), '-DABORTING_MALLOC=' + str(aborting_malloc), '-s', 'TOTAL_MEMORY=128MB'])

  # Test that -s ABORTING_MALLOC=0 works in both pthreads and non-pthreads builds. (sbrk fails gracefully)
  def test_pthread_gauge_available_memory(self):
    for opts in [[], ['-O2']]:
      for args in [[], ['-s', 'USE_PTHREADS=1']]:
        self.btest(path_from_root('tests', 'gauge_available_memory.cpp'), expected='1', args=['-s', 'ABORTING_MALLOC=0'] + args + opts)

  # Test that the proxying operations of user code from pthreads to main thread work
  def test_pthread_run_on_main_thread(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_run_on_main_thread.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test how a lot of back-to-back called proxying operations behave.
  def test_pthread_run_on_main_thread_flood(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_run_on_main_thread_flood.cpp'), expected='0', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test that it is possible to synchronously call a JavaScript function on the main thread and get a return value back.
  def test_pthread_call_sync_on_main_thread(self):
    self.btest(path_from_root('tests', 'pthread', 'call_sync_on_main_thread.c'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1', '-DPROXY_TO_PTHREAD=1', '--js-library', path_from_root('tests', 'pthread', 'call_sync_on_main_thread.js')])
    self.btest(path_from_root('tests', 'pthread', 'call_sync_on_main_thread.c'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-DPROXY_TO_PTHREAD=0', '--js-library', path_from_root('tests', 'pthread', 'call_sync_on_main_thread.js')])
    self.btest(path_from_root('tests', 'pthread', 'call_sync_on_main_thread.c'), expected='1', args=['-Oz', '-DPROXY_TO_PTHREAD=0', '--js-library', path_from_root('tests', 'pthread', 'call_sync_on_main_thread.js')])

  # Test that it is possible to asynchronously call a JavaScript function on the main thread.
  def test_pthread_call_async_on_main_thread(self):
    self.btest(path_from_root('tests', 'pthread', 'call_async_on_main_thread.c'), expected='7', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1', '-DPROXY_TO_PTHREAD=1', '--js-library', path_from_root('tests', 'pthread', 'call_async_on_main_thread.js')])
    self.btest(path_from_root('tests', 'pthread', 'call_async_on_main_thread.c'), expected='7', args=['-O3', '-s', 'USE_PTHREADS=1', '-DPROXY_TO_PTHREAD=0', '--js-library', path_from_root('tests', 'pthread', 'call_async_on_main_thread.js')])
    self.btest(path_from_root('tests', 'pthread', 'call_async_on_main_thread.c'), expected='7', args=['-Oz', '-DPROXY_TO_PTHREAD=0', '--js-library', path_from_root('tests', 'pthread', 'call_async_on_main_thread.js')])

  # Tests that spawning a new thread does not cause a reinitialization of the global data section of the application memory area.
  def test_pthread_global_data_initialization(self):
    for mem_init_mode in [[], ['--memory-init-file', '0'], ['--memory-init-file', '1'], ['-s', 'MEM_INIT_METHOD=2', '-s', 'WASM=0']]:
      for args in [[], ['-O3']]:
        self.btest(path_from_root('tests', 'pthread', 'test_pthread_global_data_initialization.c'), expected='20', args=args + mem_init_mode + ['-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # Test that emscripten_get_now() reports coherent wallclock times across all pthreads, instead of each pthread independently reporting wallclock times since the launch of that pthread.
  def test_pthread_clock_drift(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_clock_drift.cpp'), expected='1', args=['-O3', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_pthread_utf8_funcs(self):
    self.btest(path_from_root('tests', 'pthread', 'test_pthread_utf8_funcs.cpp'), expected='0', args=['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1'])

  # test atomicrmw i64
  def test_atomicrmw_i64(self):
    # TODO: enable this with wasm, currently pthreads/atomics have limitations
    run_process([PYTHON, EMCC, path_from_root('tests', 'atomicrmw_i64.ll'), '-s', 'USE_PTHREADS=1', '-s', 'IN_TEST_HARNESS=1', '-o', 'test.html', '-s', 'WASM=0'])
    self.run_browser('test.html', None, '/report_result?0')

  # Test that it is possible to send a signal via calling alarm(timeout), which in turn calls to the signal handler set by signal(SIGALRM, func);
  def test_sigalrm(self):
    self.btest(path_from_root('tests', 'sigalrm.cpp'), expected='0', args=['-O3'], timeout=30)

  def test_meminit_pairs(self):
    d = 'const char *data[] = {\n  "'
    d += '",\n  "'.join(''.join('\\x{:02x}\\x{:02x}'.format(i, j)
                                for j in range(256)) for i in range(256))
    with open(path_from_root('tests', 'meminit_pairs.c')) as f:
      d += '"\n};\n' + f.read()
    args = ["-O2", "--memory-init-file", "0", "-s", "MEM_INIT_METHOD=2", "-s", "ASSERTIONS=1", '-s', 'WASM=0']
    self.btest(d, expected='0', args=args + ["--closure", "0"])
    self.btest(d, expected='0', args=args + ["--closure", "0", "-g"])
    self.btest(d, expected='0', args=args + ["--closure", "1"])

  def test_meminit_big(self):
    d = 'const char *data[] = {\n  "'
    d += '",\n  "'.join([''.join('\\x{:02x}\\x{:02x}'.format(i, j)
                                 for j in range(256)) for i in range(256)] * 256)
    with open(path_from_root('tests', 'meminit_pairs.c')) as f:
      d += '"\n};\n' + f.read()
    assert len(d) > (1 << 27) # more than 32M memory initializer
    args = ["-O2", "--memory-init-file", "0", "-s", "MEM_INIT_METHOD=2", "-s", "ASSERTIONS=1", '-s', 'WASM=0']
    self.btest(d, expected='0', args=args + ["--closure", "0"])
    self.btest(d, expected='0', args=args + ["--closure", "0", "-g"])
    self.btest(d, expected='0', args=args + ["--closure", "1"])

  def test_canvas_style_proxy(self):
    self.btest('canvas_style_proxy.c', expected='1', args=['--proxy-to-worker', '--shell-file', path_from_root('tests/canvas_style_proxy_shell.html'), '--pre-js', path_from_root('tests/canvas_style_proxy_pre.js')])

  def test_canvas_size_proxy(self):
    self.btest(path_from_root('tests', 'canvas_size_proxy.c'), expected='0', args=['--proxy-to-worker'])

  def test_custom_messages_proxy(self):
    self.btest(path_from_root('tests', 'custom_messages_proxy.c'), expected='1', args=['--proxy-to-worker', '--shell-file', path_from_root('tests', 'custom_messages_proxy_shell.html'), '--post-js', path_from_root('tests', 'custom_messages_proxy_postjs.js')])

  def test_separate_asm(self):
    for opts in [['-O0'], ['-O1'], ['-O2'], ['-O2', '--closure', '1']]:
      print(opts)
      open('src.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'browser_test_hello_world.c')).read()))
      run_process([PYTHON, EMCC, 'src.cpp', '-o', 'test.html', '-s', 'WASM=0'] + opts)
      self.run_browser('test.html', None, '/report_result?0')

      print('run one')
      open('one.html', 'w').write('<script src="test.js"></script>')
      self.run_browser('one.html', None, '/report_result?0')

      print('run two')
      run_process([PYTHON, path_from_root('tools', 'separate_asm.py'), 'test.js', 'asm.js', 'rest.js'])
      open('two.html', 'w').write('''
        <script>
          var Module = {};
        </script>
        <script src="asm.js"></script>
        <script src="rest.js"></script>
      ''')
      self.run_browser('two.html', None, '/report_result?0')

      print('run hello world')
      self.clear()
      assert not os.path.exists('tests.asm.js')
      self.btest('browser_test_hello_world.c', expected='0', args=opts + ['-s', 'WASM=0', '--separate-asm'])
      assert os.path.exists('test.asm.js')
      os.unlink('test.asm.js')

      print('see a fail')
      self.run_browser('test.html', None, '[no http server activity]', timeout=5) # fail without the asm

  def test_emterpretify_file(self):
    open('shell.html', 'w').write('''
      <!--
        {{{ SCRIPT }}} // ignore this, we do it ourselves
      -->
      <script>
        var Module = {};
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'code.dat', true);
        xhr.responseType = 'arraybuffer';
        xhr.onload = function() {
          Module.emterpreterFile = xhr.response;
          var script = document.createElement('script');
          script.src = "test.js";
          document.body.appendChild(script);
        };
        xhr.send(null);
      </script>
''')
    try_delete('code.dat')
    self.btest('browser_test_hello_world.c', expected='0', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_FILE="code.dat"', '-O2', '-g', '--shell-file', 'shell.html', '-s', 'ASSERTIONS=1'])
    assert os.path.exists('code.dat')

    try_delete('code.dat')
    self.btest('browser_test_hello_world.c', expected='0', args=['-s', 'EMTERPRETIFY=1', '-s', 'EMTERPRETIFY_FILE="code.dat"', '-O2', '-g', '-s', 'ASSERTIONS=1'])
    assert os.path.exists('code.dat')

  def test_vanilla_html_when_proxying(self):
    for opts in [0, 1, 2]:
      print(opts)
      open('src.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'browser_test_hello_world.c')).read()))
      run_process([PYTHON, EMCC, 'src.cpp', '-o', 'test.js', '-O' + str(opts), '--proxy-to-worker'])
      open('test.html', 'w').write('<script src="test.js"></script>')
      self.run_browser('test.html', None, '/report_result?0')

  def test_in_flight_memfile_request(self):
    # test the XHR for an asm.js mem init file being in flight already
    for o in [0, 1, 2]:
      print(o)
      opts = ['-O' + str(o), '-s', 'WASM=0']

      print('plain html')
      open('src.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'in_flight_memfile_request.c')).read()))
      run_process([PYTHON, EMCC, 'src.cpp', '-o', 'test.js'] + opts)
      open('test.html', 'w').write('<script src="test.js"></script>')
      self.run_browser('test.html', None, '/report_result?0') # never when we provide our own HTML like this.

      print('default html')
      self.btest('in_flight_memfile_request.c', expected='0' if o < 2 else '1', args=opts) # should happen when there is a mem init file (-O2+)

  def test_split_memory_large_file(self):
    size = 2 * 1024 * 1024
    open('huge.dat', 'wb').write(bytearray((x * x) & 255 for x in range(size * 2))) # larger than a memory chunk
    self.btest('split_memory_large_file.cpp', expected='1', args=['-s', 'WASM=0', '-s', 'SPLIT_MEMORY=' + str(size), '-s', 'TOTAL_MEMORY=128MB', '-s', 'TOTAL_STACK=10240', '--preload-file', 'huge.dat'], timeout=60)

  def test_binaryen_interpreter(self):
    self.btest('browser_test_hello_world.c', expected='0', args=['-s', 'BINARYEN=1', '-s', 'BINARYEN_METHOD="interpret-binary"'])
    self.btest('browser_test_hello_world.c', expected='0', args=['-s', 'BINARYEN=1', '-s', 'BINARYEN_METHOD="interpret-binary"', '-O2'])

  @no_chrome("chrome doesn't support synchronous compilation over 4k")
  def test_binaryen_async(self):
    # notice when we use async compilation
    script = '''
    <script>
      // note if we do async compilation
      var real_wasm_instantiate = WebAssembly.instantiate;
      var real_wasm_instantiateStreaming = WebAssembly.instantiateStreaming;
      if (typeof real_wasm_instantiateStreaming === 'function') {
        WebAssembly.instantiateStreaming = function(a, b) {
          Module.sawAsyncCompilation = true;
          return real_wasm_instantiateStreaming(a, b);
        };
      } else {
        WebAssembly.instantiate = function(a, b) {
          Module.sawAsyncCompilation = true;
          return real_wasm_instantiate(a, b);
        };
      }
      // show stderr for the viewer's fun
      err = function(x) {
        out('<<< ' + x + ' >>>');
        console.log(x);
      };
    </script>
    {{{ SCRIPT }}}
'''
    shell_with_script('shell.html', 'shell.html', script)
    common_args = ['--shell-file', 'shell.html']
    for opts, expect in [
      ([], 1),
      (['-O1'], 1),
      (['-O2'], 1),
      (['-O3'], 1),
      (['-s', 'BINARYEN_ASYNC_COMPILATION=1'], 1), # force it on
      (['-O1', '-s', 'BINARYEN_ASYNC_COMPILATION=0'], 0), # force it off
      (['-s', 'BINARYEN_ASYNC_COMPILATION=1', '-s', 'BINARYEN_METHOD="interpret-binary"'], 0), # try to force it on, but have it disabled
    ]:
      print(opts, expect)
      self.btest('binaryen_async.c', expected=str(expect), args=common_args + opts)
    # Ensure that compilation still works and is async without instantiateStreaming available
    no_streaming = ' <script> WebAssembly.instantiateStreaming = undefined;</script>'
    shell_with_script('shell.html', 'shell.html', no_streaming + script)
    self.btest('binaryen_async.c', expected='1', args=common_args)

  # Test that implementing Module.instantiateWasm() callback works.
  def test_manual_wasm_instantiate(self):
    src = os.path.join(self.get_dir(), 'src.cpp')
    open(src, 'w').write(self.with_report_result(open(os.path.join(path_from_root('tests/manual_wasm_instantiate.cpp'))).read()))
    run_process([PYTHON, EMCC, 'src.cpp', '-o', 'manual_wasm_instantiate.js', '-s', 'BINARYEN=1'])
    shutil.copyfile(path_from_root('tests', 'manual_wasm_instantiate.html'), os.path.join(self.get_dir(), 'manual_wasm_instantiate.html'))
    self.run_browser('manual_wasm_instantiate.html', 'wasm instantiation succeeded', '/report_result?1')

  def test_binaryen_worker(self):
    self.do_test_worker(['-s', 'WASM=1'])

  def test_wasm_locate_file(self):
    # Test that it is possible to define "Module.locateFile(foo)" function to locate where pthread-main.js will be loaded from.
    self.clear()
    os.makedirs(os.path.join(self.get_dir(), 'cdn'))
    open('shell2.html', 'w').write(open(path_from_root('src', 'shell.html')).read().replace('var Module = {', 'var Module = { locateFile: function(filename) { if (filename == "test.wasm") return "cdn/test.wasm"; else return filename; }, '))
    open('src.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'browser_test_hello_world.c')).read()))
    subprocess.check_call([PYTHON, EMCC, 'src.cpp', '--shell-file', 'shell2.html', '-s', 'WASM=1', '-o', 'test.html'])
    shutil.move('test.wasm', os.path.join('cdn', 'test.wasm'))
    self.run_browser('test.html', '', '/report_result?0')

  def test_utf8_textdecoder(self):
    self.btest('benchmark_utf8.cpp', expected='0', args=['--embed-file', path_from_root('tests/utf8_corpus.txt') + '@/utf8_corpus.txt', '-s', 'EXTRA_EXPORTED_RUNTIME_METHODS=["UTF8ToString"]'])

  def test_utf16_textdecoder(self):
    self.btest('benchmark_utf16.cpp', expected='0', args=['--embed-file', path_from_root('tests/utf16_corpus.txt') + '@/utf16_corpus.txt', '-s', 'EXTRA_EXPORTED_RUNTIME_METHODS=["UTF16ToString","stringToUTF16","lengthBytesUTF16"]'])

  def test_webgl_offscreen_canvas_in_pthread(self):
    for args in [[], ['-DTEST_CHAINED_WEBGL_CONTEXT_PASSING']]:
      self.btest('gl_in_pthread.cpp', expected='1', args=args + ['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=2', '-s', 'OFFSCREENCANVAS_SUPPORT=1', '-lGL'])

  def test_webgl_offscreen_canvas_in_mainthread_after_pthread(self):
    for args in [[], ['-DTEST_MAIN_THREAD_EXPLICIT_COMMIT']]:
      self.btest('gl_in_mainthread_after_pthread.cpp', expected='0', args=args + ['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=2', '-s', 'OFFSCREENCANVAS_SUPPORT=1', '-lGL'])

  def test_webgl_offscreen_canvas_only_in_pthread(self):
    self.btest('gl_only_in_pthread.cpp', expected='0', args=['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=1', '-s', 'OFFSCREENCANVAS_SUPPORT=1', '-lGL'])

  # Tests that -s OFFSCREEN_FRAMEBUFFER=1 rendering works.
  @requires_graphics_hardware
  def test_webgl_offscreen_framebuffer(self):
    self.btest('webgl_draw_triangle.c', '0', args=['-lGL', '-s', 'OFFSCREEN_FRAMEBUFFER=1', '-DEXPLICIT_SWAP=1'])

  # Tests the feature that shell html page can preallocate the typed array and place it to Module.buffer before loading the script page.
  # In this build mode, the -s TOTAL_MEMORY=xxx option will be ignored.
  # Preallocating the buffer in this was is asm.js only (wasm needs a Memory).
  def test_preallocated_heap(self):
    self.btest('test_preallocated_heap.cpp', expected='1', args=['-s', 'WASM=0', '-s', 'TOTAL_MEMORY=16MB', '-s', 'ABORTING_MALLOC=0', '--shell-file', path_from_root('tests', 'test_preallocated_heap_shell.html')])

  # Tests emscripten_fetch() usage to XHR data directly to memory without persisting results to IndexedDB.
  def test_fetch_to_memory(self):
    # Test error reporting in the negative case when the file URL doesn't exist. (http 404)
    self.btest('fetch/to_memory.cpp',
               expected='1',
               args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-DFILE_DOES_NOT_EXIST'],
               also_asmjs=True)

    # Test the positive case when the file URL exists. (http 200)
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/to_memory.cpp',
               expected='1',
               args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1'],
               also_asmjs=True)

  def test_fetch_to_indexdb(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/to_indexeddb.cpp',
               expected='1',
               args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1'],
               also_asmjs=True)

  # Tests emscripten_fetch() usage to persist an XHR into IndexedDB and subsequently load up from there.
  def test_fetch_cached_xhr(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/cached_xhr.cpp',
               expected='1',
               args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1'],
               also_asmjs=True)

  # Tests that response headers get set on emscripten_fetch_t values.
  def test_fetch_response_headers(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/response_headers.cpp', expected='1', args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1', '-s', 'WASM=0'])

  # Test emscripten_fetch() usage to stream a XHR in to memory without storing the full file in memory
  @no_chrome('depends on moz-chunked-arraybuffer')
  def test_fetch_stream_file(self):
    # Strategy: create a large 128MB file, and compile with a small 16MB Emscripten heap, so that the tested file
    # won't fully fit in the heap. This verifies that streaming works properly.
    s = '12345678'
    for i in range(14):
      s = s[::-1] + s # length of str will be 2^17=128KB
    with open('largefile.txt', 'w') as f:
      for i in range(1024):
        f.write(s)
    self.btest('fetch/stream_file.cpp',
               expected='1',
               args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-s', 'TOTAL_MEMORY=536870912'],
               also_asmjs=True)

  # Tests emscripten_fetch() usage in synchronous mode when used from the main
  # thread proxied to a Worker with -s PROXY_TO_PTHREAD=1 option.
  def test_fetch_sync_xhr(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/sync_xhr.cpp', expected='1', args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1'])

  # Tests that the Fetch API works for synchronous XHRs when used with --proxy-to-worker.
  def test_fetch_sync_xhr_in_proxy_to_worker(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/sync_xhr.cpp',
               expected='1',
               args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '--proxy-to-worker'],
               also_asmjs=True)

  # Tests waiting on EMSCRIPTEN_FETCH_WAITABLE request from a worker thread
  def test_fetch_sync_fetch_in_main_thread(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/sync_fetch_in_main_thread.cpp', expected='0', args=['--std=c++11', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_fetch_idb_store(self):
    self.btest('fetch/idb_store.cpp', expected='0', args=['-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-s', 'WASM=0', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_fetch_idb_delete(self):
    shutil.copyfile(path_from_root('tests', 'gears.png'), os.path.join(self.get_dir(), 'gears.png'))
    self.btest('fetch/idb_delete.cpp', expected='0', args=['-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1', '-s', 'FETCH=1', '-s', 'WASM=0', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_asmfs_hello_file(self):
    # Test basic file loading and the valid character set for files.
    os.mkdir(os.path.join(self.get_dir(), 'dirrey'))
    shutil.copyfile(path_from_root('tests', 'asmfs', 'hello_file.txt'), os.path.join(self.get_dir(), 'dirrey', 'hello file !#$%&\'()+,-.;=@[]^_`{}~ %%.txt'))
    self.btest('asmfs/hello_file.cpp', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_asmfs_read_file_twice(self):
    shutil.copyfile(path_from_root('tests', 'asmfs', 'hello_file.txt'), os.path.join(self.get_dir(), 'hello_file.txt'))
    self.btest('asmfs/read_file_twice.cpp', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_asmfs_fopen_write(self):
    self.btest('asmfs/fopen_write.cpp', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_asmfs_mkdir_create_unlink_rmdir(self):
    self.btest('cstdio/test_remove.cpp', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_asmfs_dirent_test_readdir(self):
    self.btest('dirent/test_readdir.c', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_asmfs_dirent_test_readdir_empty(self):
    self.btest('dirent/test_readdir_empty.c', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_asmfs_unistd_close(self):
    self.btest('unistd/close.c', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_asmfs_unistd_access(self):
    self.btest('unistd/access.c', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_asmfs_unistd_unlink(self):
    # TODO: Once symlinks are supported, remove -DNO_SYMLINK=1
    self.btest('unistd/unlink.c', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1', '-DNO_SYMLINK=1'])

  def test_asmfs_test_fcntl_open(self):
    self.btest('fcntl-open/src.c', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1', '-s', 'PROXY_TO_PTHREAD=1'])

  def test_asmfs_relative_paths(self):
    self.btest('asmfs/relative_paths.cpp', expected='0', args=['-s', 'ASMFS=1', '-s', 'WASM=0', '-s', 'USE_PTHREADS=1', '-s', 'FETCH_DEBUG=1'])

  def test_pthread_locale(self):
    for args in [
        [],
        ['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=2'],
        ['-s', 'USE_PTHREADS=1', '-s', 'PTHREAD_POOL_SIZE=2'],
    ]:
      print("Testing with: ", args)
      self.btest('pthread/test_pthread_locale.c', expected='1', args=args)

  # Tests the Emscripten HTML5 API emscripten_set_canvas_element_size() and emscripten_get_canvas_element_size() functionality in singlethreaded programs.
  def test_emscripten_set_canvas_element_size(self):
    self.btest('emscripten_set_canvas_element_size.c', expected='1')

  # Tests the absolute minimum pthread-enabled application.
  def test_hello_thread(self):
    self.btest(path_from_root('tests', 'pthread', 'hello_thread.c'), expected='1', args=['-s', 'USE_PTHREADS=1'])

  # Tests that it is possible to load the main .js file of the application manually via a Blob URL, and still use pthreads.
  def test_load_js_from_blob_with_pthreads(self):
    # TODO: enable this with wasm, currently pthreads/atomics have limitations
    src = os.path.join(self.get_dir(), 'src.c')
    open(src, 'w').write(self.with_report_result(open(path_from_root('tests', 'pthread', 'hello_thread.c')).read()))
    run_process([PYTHON, EMCC, 'src.c', '-s', 'USE_PTHREADS=1', '-o', 'hello_thread_with_blob_url.js', '-s', 'WASM=0'])
    shutil.copyfile(path_from_root('tests', 'pthread', 'main_js_as_blob_loader.html'), os.path.join(self.get_dir(), 'hello_thread_with_blob_url.html'))
    self.run_browser('hello_thread_with_blob_url.html', 'hello from thread!', '/report_result?1')

  # Tests that base64 utils work in browser with no native atob function
  def test_base64_atob_fallback(self):
    opts = ['-s', 'SINGLE_FILE=1', '-s', 'WASM=1', '-s', "BINARYEN_METHOD='interpret-binary'"]
    src = r'''
      #include <stdio.h>
      #include <emscripten.h>
      int main() {
        REPORT_RESULT(0);
        return 0;
      }
    '''
    open('test.c', 'w').write(self.with_report_result(src))
    # generate a dummy file
    open('dummy_file', 'w').write('dummy')
    # compile the code with the modularize feature and the preload-file option enabled
    run_process([PYTHON, EMCC, 'test.c', '-s', 'MODULARIZE=1', '-s', 'EXPORT_NAME="Foo"', '--preload-file', 'dummy_file'] + opts)
    open('a.html', 'w').write('''
      <script>
        atob = undefined;
        fetch = undefined;
      </script>
      <script src="a.out.js"></script>
      <script>
        var foo = Foo();
      </script>
    ''')
    self.run_browser('a.html', '...', '/report_result?0')

  # Tests that SINGLE_FILE works as intended in generated HTML (with and without Worker)
  def test_single_file_html(self):
    self.btest('emscripten_main_loop_setimmediate.cpp', '1', args=['-s', 'SINGLE_FILE=1', '-s', 'WASM=1', '-s', "BINARYEN_METHOD='native-wasm'"], also_proxied=True)
    assert os.path.exists('test.html') and not os.path.exists('test.js') and not os.path.exists('test.worker.js')

  # Tests that SINGLE_FILE works as intended with locateFile
  def test_single_file_locate_file(self):
    open('src.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'browser_test_hello_world.c')).read()))

    for wasm_enabled in [True, False]:
      args = [PYTHON, EMCC, 'src.cpp', '-o', 'test.js', '-s', 'SINGLE_FILE=1']

      if wasm_enabled:
        args += ['-s', 'WASM=1']

      run_process(args)

      open('test.html', 'w').write('''
        <script>
          var Module = {
            locateFile: function (path) {
              if (path.indexOf('data:') === 0) {
                throw new Error('Unexpected data URI.');
              }

              return path;
            }
          };
        </script>
        <script src="test.js"></script>
      ''')

      self.run_browser('test.html', None, '/report_result?0')

  # Tests that SINGLE_FILE works as intended in a Worker in JS output
  def test_single_file_worker_js(self):
    open('src.cpp', 'w').write(self.with_report_result(open(path_from_root('tests', 'browser_test_hello_world.c')).read()))
    run_process([PYTHON, EMCC, 'src.cpp', '-o', 'test.js', '--proxy-to-worker', '-s', 'SINGLE_FILE=1', '-s', 'WASM=1', '-s', "BINARYEN_METHOD='native-wasm'"])
    open('test.html', 'w').write('<script src="test.js"></script>')
    self.run_browser('test.html', None, '/report_result?0')
    assert os.path.exists('test.js') and not os.path.exists('test.worker.js')

  def test_access_file_after_heap_resize(self):
    open('test.txt', 'w').write('hello from file')
    open('page.c', 'w').write(self.with_report_result(open(path_from_root('tests', 'access_file_after_heap_resize.c'), 'r').read()))
    run_process([PYTHON, EMCC, 'page.c', '-s', 'WASM=1', '-s', 'ALLOW_MEMORY_GROWTH=1', '--preload-file', 'test.txt', '-o', 'page.html'])
    self.run_browser('page.html', 'hello from file', '/report_result?15')

    # with separate file packager invocation, letting us affect heap copying
    # or lack thereof
    for file_packager_args in [[], ['--no-heap-copy']]:
      print(file_packager_args)
      run_process([PYTHON, FILE_PACKAGER, 'data.js', '--preload', 'test.txt', '--js-output=' + 'data.js'] + file_packager_args)
      run_process([PYTHON, EMCC, 'page.c', '-s', 'WASM=1', '-s', 'ALLOW_MEMORY_GROWTH=1', '--pre-js', 'data.js', '-o', 'page.html', '-s', 'FORCE_FILESYSTEM=1'])
      self.run_browser('page.html', 'hello from file', '/report_result?15')

  def test_unicode_html_shell(self):
    open(self.in_dir('main.cpp'), 'w').write(self.with_report_result(r'''
      int main() {
        REPORT_RESULT(0);
        return 0;
      }
    '''))
    open(self.in_dir('shell.html'), 'w').write(open(path_from_root('src', 'shell.html')).read().replace('Emscripten-Generated Code', 'Emscripten-Generated Emoji 😅'))
    subprocess.check_output([PYTHON, EMCC, os.path.join(self.get_dir(), 'main.cpp'), '--shell-file', 'shell.html', '-o', 'test.html'])
    self.run_browser('test.html', None, '/report_result?0')

  # Tests that Emscripten-compiled applications can be run from a relative path in browser that is different than the address of the current page
  def test_browser_run_from_different_directory(self):
    src = open(path_from_root('tests', 'browser_test_hello_world.c')).read()
    open('test.c', 'w').write(self.with_report_result(src))
    run_process([PYTHON, EMCC, 'test.c', '-o', 'test.html', '-O3'])

    if not os.path.exists('subdir'):
      os.mkdir('subdir')
    shutil.move('test.js', os.path.join('subdir', 'test.js'))
    shutil.move('test.wasm', os.path.join('subdir', 'test.wasm'))
    src = open('test.html').read()
    # Make sure JS is loaded from subdirectory
    open('test-subdir.html', 'w').write(src.replace('test.js', 'subdir/test.js'))
    self.run_browser('test-subdir.html', None, '/report_result?0')

  # Similar to `test_browser_run_from_different_directory`, but asynchronous because of `-s MODULARIZE=1`
  def test_browser_run_from_different_directory_async(self):
    src = open(path_from_root('tests', 'browser_test_hello_world.c')).read()
    open('test.c', 'w').write(self.with_report_result(src))
    for args, creations in [
      (['-s', 'MODULARIZE=1'], [
        'Module();',    # documented way for using modularize
        'new Module();' # not documented as working, but we support it
       ]),
      (['-s', 'MODULARIZE_INSTANCE=1'], ['']) # instance: no need to create anything
    ]:
      print(args)
      # compile the code with the modularize feature and the preload-file option enabled
      run_process([PYTHON, EMCC, 'test.c', '-o', 'test.js', '-O3'] + args)
      if not os.path.exists('subdir'):
        os.mkdir('subdir')
      shutil.move('test.js', os.path.join('subdir', 'test.js'))
      shutil.move('test.wasm', os.path.join('subdir', 'test.wasm'))
      for creation in creations:
        print(creation)
        # Make sure JS is loaded from subdirectory
        open('test-subdir.html', 'w').write('''
          <script src="subdir/test.js"></script>
          <script>
            %s
          </script>
        ''' % creation)
        self.run_browser('test-subdir.html', None, '/report_result?0')

  # Similar to `test_browser_run_from_different_directory`, but
  # also also we eval the initial code, so currentScript is not present. That prevents us
  # from finding the file in a subdir, but here we at least check we do not regress compared to the
  # normal case of finding in the current dir.
  def test_browser_modularize_no_current_script(self):
    src = open(path_from_root('tests', 'browser_test_hello_world.c')).read()
    open('test.c', 'w').write(self.with_report_result(src))
    # test both modularize (and creating an instance) and modularize-instance
    # (which creates by itself)
    for path, args, creation in [
      ([], ['-s', 'MODULARIZE=1'], 'Module();'),
      ([], ['-s', 'MODULARIZE_INSTANCE=1'], ''),
      (['subdir'], ['-s', 'MODULARIZE=1'], 'Module();'),
      (['subdir'], ['-s', 'MODULARIZE_INSTANCE=1'], ''),
    ]:
      print(path, args, creation)
      filesystem_path = os.path.join('.', *path)
      if not os.path.exists(filesystem_path):
        os.makedirs(filesystem_path)
      # compile the code with the modularize feature and the preload-file option enabled
      run_process([PYTHON, EMCC, 'test.c', '-o', 'test.js'] + args)
      shutil.move('test.js', os.path.join(filesystem_path, 'test.js'))
      shutil.move('test.wasm', os.path.join(filesystem_path, 'test.wasm'))
      open(os.path.join(filesystem_path, 'test.html'), 'w').write('''
        <script>
          setTimeout(function() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'test.js', false);
            xhr.send(null);
            eval(xhr.responseText);
            %s
          }, 1);
        </script>
      ''' % creation)
      self.run_browser('/'.join(path + ['test.html']), None, '/report_result?0')
