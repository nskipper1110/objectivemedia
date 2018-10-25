# Copyright 2013 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

from __future__ import print_function
import glob
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
import unittest
from textwrap import dedent

from tools.shared import Building, STDOUT, PIPE, run_js, run_process, Settings, try_delete
from tools.shared import NODE_JS, V8_ENGINE, JS_ENGINES, SPIDERMONKEY_ENGINE, PYTHON, EMCC, EMAR, CLANG, WINDOWS, AUTODEBUGGER
from tools import jsrun, shared
from runner import RunnerCore, path_from_root, core_test_modes, get_bullet_library
from runner import skip_if, no_wasm_backend, needs_dlfcn, no_windows, env_modify

# decorators for limiting which modes a test can run in


def SIMD(f):
  def decorated(self):
    if self.is_emterpreter():
      self.skipTest('simd not supported in emterpreter yet')
    if self.is_wasm():
      self.skipTest('wasm will not support SIMD in the MVP')
    self.use_all_engines = True # checks both native in spidermonkey and polyfill in others
    f(self)
  return decorated


def no_emterpreter(f):
  return skip_if(f, 'is_emterpreter')


def no_wasm(note=''):
  def decorated(f):
    return skip_if(f, 'is_wasm', note)
  return decorated


# Async wasm compilation can't work in some tests, they are set up synchronously
def sync(f):
  def decorated(self):
    if self.is_wasm():
      self.emcc_args += ['-s', 'BINARYEN_ASYNC_COMPILATION=0'] # test is set up synchronously
    f(self)
  return decorated


def also_with_noderawfs(func):
  def decorated(self):
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    orig_args = self.emcc_args[:]
    func(self)
    Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-DNODERAWFS']
    self.emcc_args = orig_args + ['-s', 'NODERAWFS=1']
    func(self, js_engines=[NODE_JS])
  return decorated


# A simple check whether the compiler arguments cause optimization.
def is_optimizing(args):
  return '-O' in str(args) and '-O0' not in args


class TestCoreBase(RunnerCore):
  # whether the test mode supports duplicate function elimination in js
  def supports_js_dfe(self):
    # wasm does this when optimizing anyhow
    if self.is_wasm():
      return False
    supported_opt_levels = ['-O2', '-O3', '-Oz', '-Os']
    for opt_level in supported_opt_levels:
      if opt_level in self.emcc_args:
        return True
    return False

  # Use closure in some tests for some additional coverage
  def maybe_closure(self):
    if '-O2' in self.emcc_args or '-Os' in self.emcc_args:
      self.emcc_args += ['--closure', '1']
      return True
    return False

  def do_run_in_out_file_test(self, *path, **kwargs):
      test_path = path_from_root(*path)

      def find_files(*ext_list):
        ret = None
        count = 0
        for ext in ext_list:
          if os.path.isfile(test_path + ext):
            ret = test_path + ext
            count += 1
        assert count > 0, ("No file found at {} with extension {}"
                           .format(test_path, ext_list))
        assert count <= 1, ("Test file {} found with multiple valid extensions {}"
                            .format(test_path, ext_list))
        return ret

      src = find_files('.c', '.cpp', '.cc')
      output = find_files('.out', '.txt')
      self.do_run_from_file(src, output, **kwargs)

  def test_hello_world(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')

      src = open(self.in_dir('src.cpp.o.js')).read()
      assert 'EMSCRIPTEN_GENERATED_FUNCTIONS' not in src, 'must not emit this unneeded internal thing'

  def test_intvars(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_intvars')

  def test_sintvars(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_sintvars',
                                   force_c=True)

  def test_i64(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64')

  def test_i64_2(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_2')

  def test_i64_3(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_3')

  def test_i64_4(self):
      # stuff that also needs sign corrections

      self.do_run_in_out_file_test('tests', 'core', 'test_i64_4')

  def test_i64_b(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_b')

  def test_i64_cmp(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_cmp')

  def test_i64_cmp2(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_cmp2')

  def test_i64_double(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_double')

  def test_i64_umul(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_umul')

  def test_i64_precise(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_precise')

  def test_i64_precise_unneeded(self):
      # Verify that even if we ask for precision, if it is not needed it is not included
      self.set_setting('PRECISE_I64_MATH', 1)
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_precise_unneeded')

      code = open(os.path.join(self.get_dir(), 'src.cpp.o.js')).read()
      assert 'goog.math.Long' not in code, 'i64 precise math should never be included, musl does its own printfing'

  def test_i64_precise_needed(self):
      # and now one where we do
      self.set_setting('PRECISE_I64_MATH', 1)
      self.do_run_in_out_file_test('tests', 'core', 'test_i64_precise_needed')

  def test_i64_llabs(self):
    self.set_setting('PRECISE_I64_MATH', 2)

    self.do_run_in_out_file_test('tests', 'core', 'test_i64_llabs')

  def test_i64_zextneg(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_i64_zextneg')

  def test_i64_7z(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_i64_7z',
                                 args=['hallo'])

  def test_i64_i16(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_i64_i16')

  def test_i64_qdouble(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_i64_qdouble')

  def test_i64_varargs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_i64_varargs',
                                 args='waka fleefl asdfasdfasdfasdf'
                                      .split(' '))

  def test_vararg_copy(self):
    self.do_run_in_out_file_test('tests', 'va_arg', 'test_va_copy')

  def test_llvm_fabs(self):
    self.set_setting('PRECISE_F32', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_llvm_fabs')

  def test_double_varargs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_double_varargs')

  def test_struct_varargs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_struct_varargs')

  def zzztest_nested_struct_varargs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_nested_struct_varargs')

  def test_i32_mul_precise(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_i32_mul_precise')

  def test_i16_emcc_intrinsic(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_i16_emcc_intrinsic')

  def test_double_i64_conversion(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_double_i64_conversion')

  def test_float32_precise(self):
    self.set_setting('PRECISE_F32', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_float32_precise')

  def test_negative_zero(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_negative_zero')

  def test_line_endings(self):
    self.build(open(path_from_root('tests', 'hello_world.cpp')).read(), self.get_dir(), self.in_dir('hello_world.cpp'))

  def test_literal_negative_zero(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_literal_negative_zero')

  @no_wasm_backend('test uses calls to expected js imports, rather than using llvm intrinsics directly')
  def test_llvm_intrinsics(self):
    # for bswap64
    self.set_setting('PRECISE_I64_MATH', 2)

    self.do_run_in_out_file_test('tests', 'core', 'test_llvm_intrinsics')

  def test_lower_intrinsics(self):
    self.emcc_args += ['-g1']
    self.do_run_in_out_file_test('tests', 'core', 'test_lower_intrinsics')
    # intrinsics should be lowered out
    js = open('src.cpp.o.js').read()
    assert ('llvm_' not in js) == is_optimizing(self.emcc_args), 'intrinsics must be lowered when optimizing'

  def test_bswap64(self):
    test_path = path_from_root('tests', 'core', 'test_bswap64')
    src, output = (test_path + s for s in ('.c', '.out'))

    # extra coverages
    for emulate_casts in [0, 1]:
      for emulate_fps in [0, 1, 2]:
        print(emulate_casts, emulate_fps)
        self.set_setting('EMULATE_FUNCTION_POINTER_CASTS', emulate_casts)
        self.set_setting('EMULATED_FUNCTION_POINTERS', emulate_fps)
        self.do_run_from_file(src, output)

  def test_sha1(self):
    self.do_run(open(path_from_root('tests', 'sha1.c')).read(), 'SHA1=15dd99a1991e0b3826fede3deffc1feba42278e6')

  @no_wasm_backend('test checks that __asmjs__ is #defined')
  def test_asmjs_unknown_emscripten(self):
    # No other configuration is supported, so always run this.
    self.do_run(open(path_from_root('tests', 'asmjs-unknown-emscripten.c')).read(), '')

  def test_cube2md5(self):
    self.emcc_args += ['--embed-file', 'cube2md5.txt']
    shutil.copyfile(path_from_root('tests', 'cube2md5.txt'), os.path.join(self.get_dir(), 'cube2md5.txt'))
    self.do_run(open(path_from_root('tests', 'cube2md5.cpp')).read(), open(path_from_root('tests', 'cube2md5.ok')).read())

  def test_cube2hash(self):
    # A good test of i64 math
    self.do_run('', 'Usage: hashstring <seed>',
                libraries=self.get_library('cube2hash', ['cube2hash.bc'], configure=None),
                includes=[path_from_root('tests', 'cube2hash')])

    for text, output in [('fleefl', '892BDB6FD3F62E863D63DA55851700FDE3ACF30204798CE9'),
                         ('fleefl2', 'AA2CC5F96FC9D540CA24FDAF1F71E2942753DB83E8A81B61'),
                         ('64bitisslow', '64D8470573635EC354FEE7B7F87C566FCAF1EFB491041670')]:
      self.do_run('', 'hash value: ' + output, [text], no_build=True)

  def test_unaligned(self):
      self.skipTest('LLVM marks the reads of s as fully aligned, making this test invalid')
      src = r'''
        #include <stdio.h>

        struct S {
          double x;
          int y;
        };

        int main() {
          // the 64-bit value here will not be 8-byte aligned
          S s0[3] = { {0x12a751f430142, 22}, {0x17a5c85bad144, 98}, {1, 1}};
          char buffer[10*sizeof(S)];
          int b = int(buffer);
          S *s = (S*)(b + 4-b%8);
          s[0] = s0[0];
          s[1] = s0[1];
          s[2] = s0[2];

          printf("*%d : %d : %d\n", sizeof(S), ((unsigned int)&s[0]) % 8 != ((unsigned int)&s[1]) % 8,
                                               ((unsigned int)&s[1]) - ((unsigned int)&s[0]));
          s[0].x++;
          s[0].y++;
          s[1].x++;
          s[1].y++;
          printf("%.1f,%d,%.1f,%d\n", s[0].x, s[0].y, s[1].x, s[1].y);
          return 0;
        }
        '''

      # TODO: A version of this with int64s as well

      self.do_run(src, '*12 : 1 : 12\n328157500735811.0,23,416012775903557.0,99\n')

      return # TODO: continue to the next part here

      # Test for undefined behavior in C. This is not legitimate code, but does exist

      src = r'''
        #include <stdio.h>

        int main()
        {
          int x[10];
          char *p = (char*)&x[0];
          p++;
          short *q = (short*)p;
          *q = 300;
          printf("*%d:%d*\n", *q, ((int)q)%2);
          int *r = (int*)p;
          *r = 515559;
          printf("*%d*\n", *r);
          long long *t = (long long*)p;
          *t = 42949672960;
          printf("*%lld*\n", *t);
          return 0;
        }
      '''

      try:
        self.do_run(src, '*300:1*\n*515559*\n*42949672960*\n')
      except Exception as e:
        assert 'must be aligned' in str(e), e # expected to fail without emulation

  def test_align64(self):
    src = r'''
      #include <stdio.h>

      // inspired by poppler

      enum Type {
        A = 10,
        B = 20
      };

      struct Object {
        Type type;
        union {
          int intg;
          double real;
          char *name;
        };
      };

      struct Principal {
        double x;
        Object a;
        double y;
      };

      int main(int argc, char **argv)
      {
        int base = argc-1;
        Object *o = NULL;
        printf("%d,%d\n", sizeof(Object), sizeof(Principal));
        printf("%d,%d,%d,%d\n", (int)&o[base].type, (int)&o[base].intg, (int)&o[base].real, (int)&o[base].name);
        printf("%d,%d,%d,%d\n", (int)&o[base+1].type, (int)&o[base+1].intg, (int)&o[base+1].real, (int)&o[base+1].name);
        Principal p, q;
        p.x = p.y = q.x = q.y = 0;
        p.a.type = A;
        p.a.real = 123.456;
        *(&q.a) = p.a;
        printf("%.2f,%d,%.2f,%.2f : %.2f,%d,%.2f,%.2f\n", p.x, p.a.type, p.a.real, p.y, q.x, q.a.type, q.a.real, q.y);
        return 0;
      }
    '''

    self.do_run(src, '''16,32
0,8,8,8
16,24,24,24
0.00,10,123.46,0.00 : 0.00,10,123.46,0.00
''')

  def test_align_moar(self):
    self.emcc_args = self.emcc_args + ['-msse']

    def test():
      self.do_run(r'''
#include <xmmintrin.h>
#include <stdio.h>

struct __attribute__((aligned(16))) float4x4
{
    union
    {
        float v[4][4];
        __m128 row[4];
    };
};

float4x4 v;
__m128 m;

int main()
{
    printf("Alignment: %d\n", ((int)&v) % 16);
    printf("Alignment: %d\n", ((int)&m) % 16);
}
    ''', 'Alignment: 0\nAlignment: 0\n')

    test()
    print('relocatable')
    self.set_setting('RELOCATABLE', 1)
    test()

  def test_aligned_alloc(self):
    self.do_run(open(path_from_root('tests', 'test_aligned_alloc.c')).read(), '', assert_returncode=0)

  def test_unsigned(self):
      src = '''
        #include <stdio.h>
        const signed char cvals[2] = { -1, -2 }; // compiler can store this is a string, so -1 becomes \FF, and needs re-signing
        int main()
        {
          {
            unsigned char x = 200;
            printf("*%d*\\n", x);
            unsigned char y = -22;
            printf("*%d*\\n", y);
          }

          int varey = 100;
          unsigned int MAXEY = -1, MAXEY2 = -77;
          printf("*%u,%d,%u*\\n", MAXEY, varey >= MAXEY, MAXEY2); // 100 >= -1? not in unsigned!

          int y = cvals[0];
          printf("*%d,%d,%d,%d*\\n", cvals[0], cvals[0] < 0, y, y < 0);
          y = cvals[1];
          printf("*%d,%d,%d,%d*\\n", cvals[1], cvals[1] < 0, y, y < 0);

          // zext issue - see mathop in jsifier
          unsigned char x8 = -10;
          unsigned long hold = 0;
          hold += x8;
          int y32 = hold+50;
          printf("*%u,%u*\\n", hold, y32);

          // Comparisons
          x8 = 0;
          for (int i = 0; i < 254; i++) x8++; // make it an actual 254 in JS - not a -2
          printf("*%d,%d*\\n", x8+1 == 0xff, x8+1 != 0xff); // 0xff may be '-1' in the bitcode

          return 0;
        }
      '''
      self.do_run(src, '*4294967295,0,4294967219*\n*-1,1,-1,1*\n*-2,1,-2,1*\n*246,296*\n*1,0*')

      self.emcc_args.append('-Wno-constant-conversion')
      src = '''
        #include <stdio.h>
        int main()
        {
          {
            unsigned char x;
            unsigned char *y = &x;
            *y = -1;
            printf("*%d*\\n", x);
          }
          {
            unsigned short x;
            unsigned short *y = &x;
            *y = -1;
            printf("*%d*\\n", x);
          }
          /*{ // This case is not checked. The hint for unsignedness is just the %u in printf, and we do not analyze that
            unsigned int x;
            unsigned int *y = &x;
            *y = -1;
            printf("*%u*\\n", x);
          }*/
          {
            char x;
            char *y = &x;
            *y = 255;
            printf("*%d*\\n", x);
          }
          {
            char x;
            char *y = &x;
            *y = 65535;
            printf("*%d*\\n", x);
          }
          {
            char x;
            char *y = &x;
            *y = 0xffffffff;
            printf("*%d*\\n", x);
          }
          return 0;
        }
      '''
      self.do_run(src, '*255*\n*65535*\n*-1*\n*-1*\n*-1*')

  def test_bitfields(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_bitfields')

  def test_floatvars(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_floatvars')

  def test_closebitcasts(self):
    self.do_run_in_out_file_test('tests', 'core', 'closebitcasts')

  def test_fast_math(self):
    Building.COMPILER_TEST_OPTS += ['-ffast-math']

    self.do_run_in_out_file_test('tests', 'core', 'test_fast_math',
                                 args=['5', '6', '8'])

  def test_zerodiv(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_zerodiv')

  def test_zero_multiplication(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_zero_multiplication')

  def test_isnan(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_isnan')

  def test_globaldoubles(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_globaldoubles')

  def test_math(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_math')

  def test_erf(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_erf')

  def test_math_hyperbolic(self):
    src = open(path_from_root('tests', 'hyperbolic', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'hyperbolic', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_math_lgamma(self):
    test_path = path_from_root('tests', 'math', 'lgamma')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output)

    if self.get_setting('ALLOW_MEMORY_GROWTH') == 0 and not self.is_wasm():
      print('main module')
      self.set_setting('MAIN_MODULE', 1)
      self.do_run_from_file(src, output)

  # Test that fmodf with -s PRECISE_F32=1 properly validates as asm.js (% operator cannot take in f32, only f64)
  def test_math_fmodf(self):
      test_path = path_from_root('tests', 'math', 'fmodf')
      src, output = (test_path + s for s in ('.c', '.out'))

      self.do_run_from_file(src, output)

  def test_frexp(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_frexp')

  def test_rounding(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    for precise_f32 in [0, 1]:
      print(precise_f32)
      self.set_setting('PRECISE_F32', precise_f32)

      self.do_run_in_out_file_test('tests', 'core', 'test_rounding')

  def test_fcvt(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_fcvt')

  def test_llrint(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_llrint')

  def test_getgep(self):
    # Generated code includes getelementptr (getelementptr, 0, 1), i.e., GEP as the first param to GEP
    self.do_run_in_out_file_test('tests', 'core', 'test_getgep')

  def test_multiply_defined_symbols(self):
    a1 = "int f() { return 1; }"
    a1_name = os.path.join(self.get_dir(), 'a1.c')
    open(a1_name, 'w').write(a1)
    a2 = "void x() {}"
    a2_name = os.path.join(self.get_dir(), 'a2.c')
    open(a2_name, 'w').write(a2)
    b1 = "int f() { return 2; }"
    b1_name = os.path.join(self.get_dir(), 'b1.c')
    open(b1_name, 'w').write(b1)
    b2 = "void y() {}"
    b2_name = os.path.join(self.get_dir(), 'b2.c')
    open(b2_name, 'w').write(b2)
    main = r'''
      #include <stdio.h>
      int f();
      int main() {
        printf("result: %d\n", f());
        return 0;
      }
    '''
    main_name = os.path.join(self.get_dir(), 'main.c')
    open(main_name, 'w').write(main)

    Building.emcc(a1_name)
    Building.emcc(a2_name)
    Building.emcc(b1_name)
    Building.emcc(b2_name)
    Building.emcc(main_name)

    liba_name = os.path.join(self.get_dir(), 'liba.a')
    Building.emar('cr', liba_name, [a1_name + '.o', a2_name + '.o'])
    libb_name = os.path.join(self.get_dir(), 'libb.a')
    Building.emar('cr', libb_name, [b1_name + '.o', b2_name + '.o'])

    all_name = os.path.join(self.get_dir(), 'all.bc')
    Building.link([main_name + '.o', liba_name, libb_name], all_name)

    self.do_ll_run(all_name, 'result: 1')

  def test_if(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_if')

  def test_if_else(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_if_else')

  def test_loop(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_loop')

  def test_stack(self):
    self.set_setting('INLINING_LIMIT', 50)

    self.do_run_in_out_file_test('tests', 'core', 'test_stack')

  def test_stack_align(self):
    src = path_from_root('tests', 'core', 'test_stack_align.cpp')

    def test():
      self.do_run(open(src).read(), ['''align 4: 0
align 8: 0
align 16: 0
align 32: 0
base align: 0, 0, 0, 0'''])

    test()
    if '-O' in str(self.emcc_args):
      print('outlining')
      self.set_setting('OUTLINING_LIMIT', 60)
      test()

  @no_emterpreter
  def test_stack_restore(self):
    if self.is_wasm():
      self.skipTest('generated code not available in wasm')
    self.emcc_args += ['-g3'] # to be able to find the generated code
    test_path = path_from_root('tests', 'core', 'test_stack_restore')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output)

    generated = open('src.cpp.o.js').read()

    def ensure_stack_restore_count(function_name, expected_count):
      code = generated[generated.find(function_name):]
      code = code[:code.find('\n}') + 2]
      actual_count = code.count('STACKTOP = sp')
      assert actual_count == expected_count, ('Expected %d stack restorations, got %d' % (expected_count, actual_count)) + ': ' + code

    ensure_stack_restore_count('function _no_stack_usage', 0)
    ensure_stack_restore_count('function _alloca_gets_restored', 1)
    ensure_stack_restore_count('function _stack_usage', 1)

  def test_strings(self):
    test_path = path_from_root('tests', 'core', 'test_strings')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output, ['wowie', 'too', '74'])

  def test_strcmp_uni(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strcmp_uni')

  def test_strndup(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strndup')

  def test_errar(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_errar')

  def test_mainenv(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_mainenv')

  def test_funcs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_funcs')

  def test_structs(self):
    test_path = path_from_root('tests', 'core', 'test_structs')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output)

  gen_struct_src = '''
        #include <stdio.h>
        #include <stdlib.h>
        #include "emscripten.h"

        struct S
        {
          int x, y;
        };
        int main()
        {
          S* a = {{gen_struct}};
          a->x = 51; a->y = 62;
          printf("*%d,%d*\\n", a->x, a->y);
          {{del_struct}}(a);
          return 0;
        }
  '''

  def test_mallocstruct(self):
    self.do_run(self.gen_struct_src.replace('{{gen_struct}}', '(S*)malloc(sizeof(S))').replace('{{del_struct}}', 'free'), '*51,62*')

  def test_emmalloc(self):
    # in newer clang+llvm, the internal calls to malloc in emmalloc may be optimized under
    # the assumption that they are external, so like in system_libs.py where we build
    # malloc, we need to disable builtin here too
    self.emcc_args += ['-fno-builtin']

    def test():
      self.do_run(open(path_from_root('system', 'lib', 'emmalloc.cpp')).read() + open(path_from_root('tests', 'core', 'test_emmalloc.cpp')).read(),
                  open(path_from_root('tests', 'core', 'test_emmalloc.txt')).read())
    print('normal')
    test()
    print('debug')
    self.emcc_args += ['-DEMMALLOC_DEBUG']
    test()
    print('debug log')
    self.emcc_args += ['-DEMMALLOC_DEBUG_LOG']
    self.emcc_args += ['-DRANDOM_ITERS=130']
    test()

  def test_newstruct(self):
    self.do_run(self.gen_struct_src.replace('{{gen_struct}}', 'new S').replace('{{del_struct}}', 'delete'), '*51,62*')

  def test_addr_of_stacked(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_addr_of_stacked')

  def test_globals(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_globals')

  def test_linked_list(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_linked_list')

  def test_sup(self):
      src = '''
        #include <stdio.h>

        struct S4   { int x;          }; // size: 4
        struct S4_2 { short x, y;     }; // size: 4, but for alignment purposes, 2
        struct S6   { short x, y, z;  }; // size: 6
        struct S6w  { char x[6];      }; // size: 6 also
        struct S6z  { int x; short y; }; // size: 8, since we align to a multiple of the biggest - 4

        struct C___  { S6 a, b, c; int later; };
        struct Carr  { S6 a[3]; int later; }; // essentially the same, but differently defined
        struct C__w  { S6 a; S6w b; S6 c; int later; }; // same size, different struct
        struct Cp1_  { int pre; short a; S6 b, c; int later; }; // fillers for a
        struct Cp2_  { int a; short pre; S6 b, c; int later; }; // fillers for a (get addr of the other filler)
        struct Cint  { S6 a; int  b; S6 c; int later; }; // An int (different size) for b
        struct C4__  { S6 a; S4   b; S6 c; int later; }; // Same size as int from before, but a struct
        struct C4_2  { S6 a; S4_2 b; S6 c; int later; }; // Same size as int from before, but a struct with max element size 2
        struct C__z  { S6 a; S6z  b; S6 c; int later; }; // different size, 8 instead of 6

        int main()
        {
          #define TEST(struc) \\
          { \\
            struc *s = 0; \\
            printf("*%s: %d,%d,%d,%d<%d*\\n", #struc, (int)&(s->a), (int)&(s->b), (int)&(s->c), (int)&(s->later), sizeof(struc)); \\
          }
          #define TEST_ARR(struc) \\
          { \\
            struc *s = 0; \\
            printf("*%s: %d,%d,%d,%d<%d*\\n", #struc, (int)&(s->a[0]), (int)&(s->a[1]), (int)&(s->a[2]), (int)&(s->later), sizeof(struc)); \\
          }
          printf("sizeofs:%d,%d\\n", sizeof(S6), sizeof(S6z));
          TEST(C___);
          TEST_ARR(Carr);
          TEST(C__w);
          TEST(Cp1_);
          TEST(Cp2_);
          TEST(Cint);
          TEST(C4__);
          TEST(C4_2);
          TEST(C__z);
          return 0;
        }
      '''
      self.do_run(src, 'sizeofs:6,8\n*C___: 0,6,12,20<24*\n*Carr: 0,6,12,20<24*\n*C__w: 0,6,12,20<24*\n*Cp1_: 4,6,12,20<24*\n*Cp2_: 0,6,12,20<24*\n*Cint: 0,8,12,20<24*\n*C4__: 0,8,12,20<24*\n*C4_2: 0,6,10,16<20*\n*C__z: 0,8,16,24<28*')

  def test_assert(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_assert')

  def test_libcextra(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_libcextra')

  def test_regex(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_regex')

  def test_longjmp(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp')

  def test_longjmp2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp2')

  def test_longjmp3(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp3')

  def test_longjmp4(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp4')

  def test_longjmp_funcptr(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp_funcptr')

  def test_longjmp_repeat(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp_repeat')

  def test_longjmp_stacked(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp_stacked')

  def test_longjmp_exc(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp_exc')

  def test_longjmp_throw(self):
    for disable_throw in [0, 1]:
      print(disable_throw)
      self.set_setting('DISABLE_EXCEPTION_CATCHING', disable_throw)
      self.do_run_in_out_file_test('tests', 'core', 'test_longjmp_throw')

  def test_longjmp_unwind(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_longjmp_unwind')

  def test_siglongjmp(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_siglongjmp')

  def test_setjmp_many(self):
    src = r'''
      #include <stdio.h>
      #include <setjmp.h>

      int main(int argc, char** argv) {
        jmp_buf buf;
        for (int i = 0; i < NUM; i++) printf("%d\n", setjmp(buf));
        if (argc-- == 1131) longjmp(buf, 11);
        return 0;
      }
    '''
    for num in [1, 5, 20, 1000]:
      print('NUM=%d' % num)
      self.do_run(src.replace('NUM', str(num)), '0\n' * num)

  def test_setjmp_many_2(self):
    src = r'''
#include <setjmp.h>
#include <stdio.h>

jmp_buf env;

void luaWork(int d){
    int x;
    printf("d is at %d\n", d);

    longjmp(env, 1);
}

int main()
{
    const int ITERATIONS=25;
    for(int i = 0; i < ITERATIONS; i++){
        if(!setjmp(env)){
            luaWork(i);
        }
    }
    return 0;
}
'''

    self.do_run(src, r'''d is at 24''')

  def test_setjmp_noleak(self):
    src = r'''
#include <setjmp.h>
#include <stdio.h>
#include <assert.h>

jmp_buf env;

void luaWork(int d){
  int x;
  printf("d is at %d\n", d);

  longjmp(env, 1);
}

#include <malloc.h>
#include <stdlib.h>

void dump() {
  struct mallinfo m = mallinfo();
  printf("dump: %d , %d\n", m.arena, m.uordblks);
}

void work(int n)
{
  printf("work %d\n", n);
  dump();

  if(!setjmp(env)){
    luaWork(n);
  }

  if (n > 0) work(n-1);
}

int main() {
  struct mallinfo m1 = mallinfo();
  dump();
  work(10);
  dump();
  struct mallinfo m2 = mallinfo();
  assert(m1.uordblks == m2.uordblks);
  printf("ok.\n");
}
'''

    self.do_run(src, r'''ok.''')

  def test_exceptions(self):
    self.set_setting('EXCEPTION_DEBUG', 1)
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)

    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.maybe_closure()

    src = '''
      #include <stdio.h>
      void thrower() {
        printf("infunc...");
        throw(99);
        printf("FAIL");
      }
      int main() {
        try {
          printf("*throw...");
          throw(1);
          printf("FAIL");
        } catch(...) {
          printf("caught!");
        }
        try {
          thrower();
        } catch(...) {
          printf("done!*\\n");
        }
        return 0;
      }
    '''
    self.do_run(src, '*throw...caught!infunc...done!*')

    self.set_setting('DISABLE_EXCEPTION_CATCHING', 1)
    self.do_run(src, 'Exception catching is disabled, this exception cannot be caught. Compile with -s DISABLE_EXCEPTION_CATCHING=0')

  def test_exceptions_custom(self):
    self.set_setting('EXCEPTION_DEBUG', 1)
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.maybe_closure()
    src = '''
    #include <iostream>

    class MyException
    {
    public:
        MyException(){ std::cout << "Construct..."; }
        MyException( const MyException & ) { std::cout << "Copy..."; }
        ~MyException(){ std::cout << "Destruct..."; }
    };

    int function()
    {
        std::cout << "Throw...";
        throw MyException();
    }

    int function2()
    {
        return function();
    }

    int main()
    {
        try
        {
            function2();
        }
        catch (MyException & e)
        {
            std::cout << "Caught...";
        }

        try
        {
            function2();
        }
        catch (MyException e)
        {
            std::cout << "Caught...";
        }

        return 0;
    }
    '''

    self.do_run(src, 'Throw...Construct...Caught...Destruct...Throw...Construct...Copy...Caught...Destruct...Destruct...')

  def test_exceptions_2(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    for safe in [0, 1]:
      print(safe)
      self.set_setting('SAFE_HEAP', safe)
      self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_2')

  def test_exceptions_3(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)

    src = r'''
#include <iostream>
#include <stdexcept>

int main(int argc, char **argv)
{
  if (argc != 2) {
    std::cout << "need an arg" << std::endl;
    return 1;
  }

  int arg = argv[1][0] - '0';
  try {
    if (arg == 0) throw "a c string";
    if (arg == 1) throw std::exception();
    if (arg == 2) throw std::runtime_error("Hello");
  } catch(const char * ex) {
    std::cout << "Caught C string: " << ex << std::endl;
  } catch(const std::exception &ex) {
    std::cout << "Caught exception: " << ex.what() << std::endl;
  } catch(...) {
    std::cout << "Caught something else" << std::endl;
  }

  std::cout << "Done.\n";
}
'''

    print('0')
    self.do_run(src, 'Caught C string: a c string\nDone.', ['0'])
    print('1')
    self.do_run(src, 'Caught exception: std::exception\nDone.', ['1'], no_build=True)
    print('2')
    self.do_run(src, 'Caught exception: Hello\nDone.', ['2'], no_build=True)

  def test_exceptions_white_list(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 2)
    # Wasm does not add an underscore to function names. For wasm, the
    # mismatches are fixed in fixImports() function in JS glue code.
    if not self.is_wasm_backend():
      self.set_setting('EXCEPTION_CATCHING_WHITELIST', ["__Z12somefunctionv"])
    else:
      self.set_setting('EXCEPTION_CATCHING_WHITELIST', ["_Z12somefunctionv"])
    # otherwise it is inlined and not identified
    self.set_setting('INLINING_LIMIT', 50)

    test_path = path_from_root('tests', 'core', 'test_exceptions_white_list')
    src, output = (test_path + s for s in ('.cpp', '.out'))
    self.do_run_from_file(src, output)
    size = len(open('src.cpp.o.js').read())
    shutil.copyfile('src.cpp.o.js', 'orig.js')

    # check that an empty whitelist works properly (as in, same as exceptions disabled)
    empty_output = path_from_root('tests', 'core', 'test_exceptions_white_list_empty.out')

    self.set_setting('EXCEPTION_CATCHING_WHITELIST', [])
    self.do_run_from_file(src, empty_output)
    empty_size = len(open('src.cpp.o.js').read())
    shutil.copyfile('src.cpp.o.js', 'empty.js')

    self.set_setting('EXCEPTION_CATCHING_WHITELIST', ['fake'])
    self.do_run_from_file(src, empty_output)
    fake_size = len(open('src.cpp.o.js').read())
    shutil.copyfile('src.cpp.o.js', 'fake.js')

    self.set_setting('DISABLE_EXCEPTION_CATCHING', 1)
    self.do_run_from_file(src, empty_output)
    disabled_size = len(open('src.cpp.o.js').read())
    shutil.copyfile('src.cpp.o.js', 'disabled.js')

    if not self.is_wasm():
      print(size, empty_size, fake_size, disabled_size)

      assert size - empty_size > 0.0025 * size, [empty_size, size]  # big change when we disable entirely
      assert size - fake_size > 0.0025 * size, [fake_size, size]
      assert abs(empty_size - fake_size) < 0.007 * size, [empty_size, fake_size]
      assert empty_size - disabled_size < 0.007 * size, [empty_size, disabled_size]  # full disable removes a little bit more
      assert fake_size - disabled_size < 0.007 * size, [disabled_size, fake_size]

  def test_exceptions_white_list_2(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 2)
    # Wasm does not add an underscore to function names. For wasm, the
    # mismatches are fixed in fixImports() function in JS glue code.
    if not self.is_wasm_backend():
      self.set_setting('EXCEPTION_CATCHING_WHITELIST', ["_main"])
    else:
      self.set_setting('EXCEPTION_CATCHING_WHITELIST', ["main"])
    # otherwise it is inlined and not identified
    self.set_setting('INLINING_LIMIT', 1)

    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_white_list_2')

  def test_exceptions_uncaught(self):
      self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
      # needs to flush stdio streams
      self.set_setting('EXIT_RUNTIME', 1)
      src = r'''
        #include <stdio.h>
        #include <exception>
        struct X {
          ~X() {
            printf("exception? %s\n", std::uncaught_exception() ? "yes" : "no");
          }
        };
        int main() {
          printf("exception? %s\n", std::uncaught_exception() ? "yes" : "no");
          try {
            X x;
            throw 1;
          } catch(...) {
            printf("exception? %s\n", std::uncaught_exception() ? "yes" : "no");
          }
          printf("exception? %s\n", std::uncaught_exception() ? "yes" : "no");
          return 0;
        }
      '''
      self.do_run(src, 'exception? no\nexception? yes\nexception? no\nexception? no\n')

      src = r'''
        #include <fstream>
        #include <iostream>
        int main() {
          std::ofstream os("test");
          os << std::unitbuf << "foo"; // trigger a call to std::uncaught_exception from
                                       // std::basic_ostream::sentry::~sentry
          std::cout << "success";
        }
      '''
      self.do_run(src, 'success')

  def test_exceptions_uncaught_2(self):
      self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
      # needs to flush stdio streams
      self.set_setting('EXIT_RUNTIME', 1)
      src = r'''
        #include <iostream>
        #include <exception>

        int main() {
          try {
              throw std::exception();
          } catch(std::exception) {
            try {
              throw;
            } catch(std::exception) {}
          }

          if (std::uncaught_exception())
            std::cout << "ERROR: uncaught_exception still set.";
          else
            std::cout << "OK";
        }
      '''
      self.do_run(src, 'OK\n')

  def test_exceptions_typed(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.emcc_args += ['-s', 'SAFE_HEAP=0'] # Throwing null will cause an ignorable null pointer access.

    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_typed')

  def test_exceptions_virtual_inheritance(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)

    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_virtual_inheritance')

  def test_exceptions_convert(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_convert')

  def test_exceptions_multi(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_multi')

  def test_exceptions_std(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.set_setting('ERROR_ON_UNDEFINED_SYMBOLS', 1)
    self.emcc_args += ['-s', 'SAFE_HEAP=0']

    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_std')

  def test_exceptions_alias(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_alias')

  def test_exceptions_rethrow(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_rethrow')

  def test_exceptions_resume(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.set_setting('EXCEPTION_DEBUG', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_resume')

  def test_exceptions_destroy_virtual(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_destroy_virtual')

  def test_exceptions_refcount(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_refcount')

  def test_exceptions_primary(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_primary')

  def test_exceptions_simplify_cfg(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_simplify_cfg')

  def test_exceptions_libcxx(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_libcxx')

  def test_exceptions_multiple_inherit(self):
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.do_run_in_out_file_test('tests', 'core', 'test_exceptions_multiple_inherit')

  def test_bad_typeid(self):
    self.set_setting('ERROR_ON_UNDEFINED_SYMBOLS', 1)
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)

    self.do_run(r'''
// exception example
#include <iostream>       // std::cerr
#include <typeinfo>       // operator typeid
#include <exception>      // std::exception

class Polymorphic {virtual void member(){}};

int main () {
  try
  {
    Polymorphic * pb = 0;
    const std::type_info& ti = typeid(*pb);  // throws a bad_typeid exception
  }
  catch (std::exception& e)
  {
    std::cerr << "exception caught: " << e.what() << '\n';
  }
  return 0;
}
    ''', 'exception caught: std::bad_typeid')

  def test_iostream_ctors(self): # iostream stuff must be globally constructed before user global constructors, so iostream works in global constructors
    self.do_run(r'''
#include <iostream>

struct A {
  A() { std::cout << "bug"; }
};
A a;

int main() {
  std::cout << "free code" << std::endl;
  return 0;
}
''', "bugfree code")

  def test_class(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_class')

  def test_inherit(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_inherit')

  def test_isdigit_l(self):
      # needs to flush stdio streams
      self.set_setting('EXIT_RUNTIME', 1)
      self.do_run_in_out_file_test('tests', 'core', 'test_isdigit_l')

  def test_iswdigit(self):
      # needs to flush stdio streams
      self.set_setting('EXIT_RUNTIME', 1)
      self.do_run_in_out_file_test('tests', 'core', 'test_iswdigit')

  def test_polymorph(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_polymorph')

  def test_complex(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_complex', force_c=True)

  def test_float_builtins(self):
    # tests wasm_libc_rt
    if not self.is_wasm_backend():
      self.skipTest('no __builtin_fmin support in JSBackend')
    self.do_run_in_out_file_test('tests', 'core', 'test_float_builtins')

  def test_segfault(self):
    self.set_setting('SAFE_HEAP', 1)

    for addr in ['0', 'new D2()']:
      print(addr)
      src = r'''
        #include <stdio.h>

        struct Classey {
          virtual void doIt() = 0;
        };

        struct D1 : Classey {
          virtual void doIt() { printf("fleefl\n"); }
        };

        struct D2 : Classey {
          virtual void doIt() { printf("marfoosh\n"); }
        };

        int main(int argc, char **argv)
        {
          Classey *p = argc == 100 ? new D1() : (Classey*)%s;

          p->doIt();

          return 0;
        }
      ''' % addr
      self.do_run(src, 'segmentation fault' if addr.isdigit() else 'marfoosh')

  def test_dynamic_cast(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_dynamic_cast')

  def test_dynamic_cast_b(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_dynamic_cast_b')

  def test_dynamic_cast_2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_dynamic_cast_2')

  def test_funcptr(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_funcptr')

  def test_mathfuncptr(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_mathfuncptr')

    if self.is_emterpreter():
      print('emterpreter f32')
      self.set_setting('PRECISE_F32', 1)
      self.do_run_in_out_file_test('tests', 'core', 'test_mathfuncptr')

  def test_funcptrfunc(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_funcptrfunc')

  def test_funcptr_namecollide(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_funcptr_namecollide')

  def test_emptyclass(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_emptyclass')

  def test_alloca(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_alloca')

  def test_rename(self):
    self.do_run_in_out_file_test('tests', 'stdio', 'test_rename', force_c=True)

  def test_remove(self):
   # needs to flush stdio streams
   self.set_setting('EXIT_RUNTIME', 1)
   self.do_run_in_out_file_test('tests', 'cstdio', 'test_remove')

  def test_alloca_stack(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_alloca_stack')

  def test_stack_byval(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_stack_byval')

  def test_stack_varargs(self):
    self.set_setting('INLINING_LIMIT', 50)
    self.set_setting('TOTAL_STACK', 2048)

    self.do_run_in_out_file_test('tests', 'core', 'test_stack_varargs')

  def test_stack_varargs2(self):
    self.set_setting('TOTAL_STACK', 1536)
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>

      void func(int i) {
      }
      int main() {
        for (int i = 0; i < 1024; i++) {
          printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
                   i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i);
        }
        printf("ok!\n");
        return 0;
      }
    '''
    self.do_run(src, 'ok!')

    print('with return')

    src = r'''
      #include <stdio.h>
      #include <stdlib.h>

      int main() {
        for (int i = 0; i < 1024; i++) {
          int j = printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
                   i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i);
          printf(" (%d)\n", j);
        }
        printf("ok!\n");
        return 0;
      }
    '''
    self.do_run(src, 'ok!')

    print('with definitely no return')

    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <stdarg.h>

      void vary(const char *s, ...)
      {
        va_list v;
        va_start(v, s);
        char d[20];
        vsnprintf(d, 20, s, v);
        puts(d);

        // Try it with copying
        va_list tempva;
        va_copy(tempva, v);
        vsnprintf(d, 20, s, tempva);
        puts(d);

        va_end(v);
      }

      int main() {
        for (int i = 0; i < 1024; i++) {
          int j = printf("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
                   i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i, i);
          printf(" (%d)\n", j);
          vary("*cheez: %d+%d*", 99, 24);
          vary("*albeit*");
        }
        printf("ok!\n");
        return 0;
      }
    '''
    self.do_run(src, 'ok!')

  def test_stack_void(self):
    self.set_setting('INLINING_LIMIT', 50)

    self.do_run_in_out_file_test('tests', 'core', 'test_stack_void')

  # Fails in wasm because of excessive slowness in the wasm-shell
  @no_wasm()
  def test_life(self):
    self.emcc_args += ['-std=c99']
    src = open(path_from_root('tests', 'life.c'), 'r').read()
    self.do_run(src, '''--------------------------------
[]                                    []                  [][][]
                    []  []    []    [][]  []            []  []  
[]                [][]  [][]              [][][]      []        
                  []    []      []      []  [][]    []        []
                  []  [][]    []        []    []  []    [][][][]
                    [][]      [][]  []    [][][]  []        []  
                                []  [][]  [][]    [][]  [][][]  
                                    [][]          [][][]  []  []
                                    [][]              [][]    []
                                                          [][][]
                                                            []  
                                                                
                                                                
                                                                
                                                                
                                        [][][]                  
                                      []      [][]      [][]    
                                      [][]      []  [][]  [][]  
                                                    [][]  [][]  
                                                      []        
                  [][]                                          
                  [][]                                        []
[]                                                      [][]  []
                                                  [][][]      []
                                                []      [][]    
[]                                                    []      []
                                                          []    
[]                                                        []  []
                                              [][][]            
                                                                
                                  []                            
                              [][][]                          []
--------------------------------
''', ['2'], force_c=True)  # noqa

  def test_array2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_array2')

  def test_array2b(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_array2b')

  def test_constglobalstructs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_constglobalstructs')

  def test_conststructs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_conststructs')

  def test_bigarray(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_bigarray')

  def test_mod_globalstruct(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_mod_globalstruct')

  @no_wasm_backend('long doubles are f128s in wasm backend')
  def test_pystruct(self):
    def test():
      self.do_run_in_out_file_test('tests', 'test_pystruct')

    test()

    print('relocatable') # this tests recursive global structs => nontrivial postSets for relocation
    assert self.get_setting('RELOCATABLE') == self.get_setting('EMULATED_FUNCTION_POINTERS') == 0
    self.set_setting('RELOCATABLE', 1)
    self.set_setting('EMULATED_FUNCTION_POINTERS', 1)
    test()

  def test_sizeof(self):
      # Has invalid writes between printouts
      self.set_setting('SAFE_HEAP', 0)

      self.do_run_in_out_file_test('tests', 'core', 'test_sizeof')

  def test_llvm_used(self):
    Building.LLVM_OPTS = 3

    self.do_run_in_out_file_test('tests', 'core', 'test_llvm_used')

  def test_set_align(self):
    self.set_setting('SAFE_HEAP', 1)

    self.do_run_in_out_file_test('tests', 'core', 'test_set_align')

  def test_emscripten_api(self):
      check = '''
def process(filename):
  src = open(filename, 'r').read()
  # TODO: restore this (see comment in emscripten.h) assert '// hello from the source' in src
'''
      self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_save_me_aimee'])
      self.do_run_in_out_file_test('tests', 'core', 'test_emscripten_api',
                                   js_transform=check)

      # test EXPORT_ALL
      self.set_setting('EXPORTED_FUNCTIONS', [])
      self.set_setting('EXPORT_ALL', 1)
      self.set_setting('LINKABLE', 1)
      self.do_run_in_out_file_test('tests', 'core', 'test_emscripten_api',
                                   js_transform=check)

  def test_emscripten_run_script_string_utf8(self):
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <string.h>
      #include <emscripten.h>

      int main() {
        const char *str = emscripten_run_script_string("'\\u2603 \\u2603 \\u2603 Hello!'");
        printf("length of returned string: %d. Position of substring 'Hello': %d\n", strlen(str), strstr(str, "Hello")-str);
        return 0;
      }
    '''
    self.do_run(src, '''length of returned string: 18. Position of substring 'Hello': 12''')

  def test_emscripten_get_now(self):
    self.banned_js_engines = [V8_ENGINE] # timer limitations in v8 shell
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)

    if self.run_name == 'asm2':
      self.emcc_args += ['--closure', '1'] # Use closure here for some additional coverage
    self.do_run(open(path_from_root('tests', 'emscripten_get_now.cpp')).read(), 'Timer resolution is good')

  def test_emscripten_get_compiler_setting(self):
    test_path = path_from_root('tests', 'core', 'emscripten_get_compiler_setting')
    src, output = (test_path + s for s in ('.c', '.out'))
    old = self.get_setting('ASSERTIONS')
    # with assertions, a nice message is shown
    self.set_setting('ASSERTIONS', 1)
    self.do_run(open(src).read(), 'You must build with -s RETAIN_COMPILER_SETTINGS=1')
    self.set_setting('ASSERTIONS', old)
    self.set_setting('RETAIN_COMPILER_SETTINGS', 1)
    self.do_run(open(src).read(), open(output).read().replace('waka', shared.EMSCRIPTEN_VERSION))

  # TODO: test only worked in non-fastcomp
  def test_inlinejs(self):
    self.skipTest('non-fastcomp is deprecated and fails in 3.5') # only supports EM_ASM

    self.do_run_in_out_file_test('tests', 'core', 'test_inlinejs')

    if self.emcc_args == []:
      # opts will eliminate the comments
      out = open('src.cpp.o.js').read()
      for i in range(1, 5):
        assert ('comment%d' % i) in out

  # TODO: test only worked in non-fastcomp
  def test_inlinejs2(self):
    self.skipTest('non-fastcomp is deprecated and fails in 3.5') # only supports EM_ASM

    self.do_run_in_out_file_test('tests', 'core', 'test_inlinejs2')

  def test_inlinejs3(self):
    if self.is_wasm():
      self.skipTest('wasm requires a proper asm module')

    test_path = path_from_root('tests', 'core', 'test_inlinejs3')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output)

    print('no debugger, check validation')
    src = open(src).read().replace('emscripten_debugger();', '')
    self.do_run(src, open(output).read())

  def test_inlinejs4(self):
    self.do_run(r'''
#include <emscripten.h>

#define TO_STRING_INNER(x) #x
#define TO_STRING(x) TO_STRING_INNER(x)
#define assert_msg(msg, file, line) EM_ASM( throw 'Assert (' + msg + ') failed in ' + file + ':' + line + '!'; )
#define assert(expr) { \
  if (!(expr)) { \
    assert_msg(#expr, TO_STRING(__FILE__), TO_STRING(__LINE__)); \
  } \
}

int main(int argc, char **argv) {
  assert(argc != 17);
  assert(false);
  return 0;
}
''', 'false')

  def test_em_asm(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm')
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm', force_c=True)

  # Tests various different ways to invoke the EM_ASM(), EM_ASM_INT() and EM_ASM_DOUBLE() macros.
  def test_em_asm_2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm_2')
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm_2', force_c=True)

  # Tests various different ways to invoke the MAIN_THREAD_EM_ASM(), MAIN_THREAD_EM_ASM_INT() and MAIN_THREAD_EM_ASM_DOUBLE() macros.
  # This test is identical to test_em_asm_2, just search-replaces EM_ASM to MAIN_THREAD_EM_ASM on the test file. That way if new
  # test cases are added to test_em_asm_2.cpp for EM_ASM, they will also get tested in MAIN_THREAD_EM_ASM form.
  @no_wasm_backend('Proxying EM_ASM calls is not yet implemented in Wasm backend')
  def test_main_thread_em_asm(self):
    self.skipTest('TODO: Enable me when we have tagged new compiler build')
    src = open(path_from_root('tests', 'core', 'test_em_asm_2.cpp'), 'r').read()
    test_file = 'src.cpp'
    open(test_file, 'w').write(src.replace('EM_ASM', 'MAIN_THREAD_EM_ASM'))

    expected_result = open(path_from_root('tests', 'core', 'test_em_asm_2.out'), 'r').read()
    expected_result_file = 'result.out'
    open(expected_result_file, 'w').write(expected_result.replace('EM_ASM', 'MAIN_THREAD_EM_ASM'))

    self.do_run_from_file(test_file, expected_result_file)
    self.do_run_from_file(test_file, expected_result_file, force_c=True)

  @no_wasm_backend('Proxying EM_ASM calls is not yet implemented in Wasm backend')
  def test_main_thread_async_em_asm(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_main_thread_async_em_asm')
    self.do_run_in_out_file_test('tests', 'core', 'test_main_thread_async_em_asm', force_c=True)

  def test_em_asm_unicode(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm_unicode')
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm_unicode', force_c=True)

  def test_em_asm_unused_arguments(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm_unused_arguments')

  # Verify that EM_ASM macros support getting called with multiple arities.
  # Maybe tests will later be joined into larger compilation units?
  # Then this must still be compiled separately from other code using EM_ASM
  # macros with arities 1-3. Otherwise this may incorrectly report a success.
  def test_em_asm_parameter_pack(self):
    Building.COMPILER_TEST_OPTS += ['-std=c++11']
    self.do_run_in_out_file_test('tests', 'core', 'test_em_asm_parameter_pack')

  def test_em_js(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_em_js')
    self.do_run_in_out_file_test('tests', 'core', 'test_em_js', force_c=True)

  def test_runtime_stacksave(self):
    src = open(path_from_root('tests', 'core', 'test_runtime_stacksave.c')).read()
    self.do_run(src, 'success')

  def test_memorygrowth(self):
    self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=0'] # start with 0

    # With typed arrays in particular, it is dangerous to use more memory than TOTAL_MEMORY,
    # since we then need to enlarge the heap(s).
    src = open(path_from_root('tests', 'core', 'test_memorygrowth.c')).read()

    # Fail without memory growth
    self.do_run(src, 'Cannot enlarge memory arrays.')
    fail = open('src.cpp.o.js').read()

    # Win with it
    self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=1']
    self.do_run(src, '*pre: hello,4.955*\n*hello,4.955*\n*hello,4.955*')
    win = open('src.cpp.o.js').read()

    if '-O2' in self.emcc_args and not self.is_wasm():
      # Make sure ALLOW_MEMORY_GROWTH generates different code (should be less optimized)
      possible_starts = ['// EMSCRIPTEN_START_FUNCS', 'var TOTAL_MEMORY']
      code_start = None
      for s in possible_starts:
        if fail.find(s) >= 0:
          code_start = s
          break
      assert code_start is not None, 'Generated code must contain one of ' + str(possible_starts)

      fail = fail[fail.find(code_start):]
      win = win[win.find(code_start):]
      assert len(fail) < len(win), 'failing code - without memory growth on - is more optimized, and smaller' + str([len(fail), len(win)])

    # Tracing of memory growths should work
    self.set_setting('EMSCRIPTEN_TRACING', 1)
    self.emcc_args += ['--tracing']
    self.do_run(src, '*pre: hello,4.955*\n*hello,4.955*\n*hello,4.955*')

  def test_memorygrowth_2(self):
    self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=0'] # start with 0

    emcc_args = self.emcc_args[:]

    def test():
      self.emcc_args = emcc_args[:]

      # With typed arrays in particular, it is dangerous to use more memory than TOTAL_MEMORY,
      # since we then need to enlarge the heap(s).
      src = open(path_from_root('tests', 'core', 'test_memorygrowth_2.c')).read()

      # Fail without memory growth
      self.do_run(src, 'Cannot enlarge memory arrays.')
      fail = open('src.cpp.o.js').read()

      # Win with it
      self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=1']
      self.do_run(src, '*pre: hello,4.955*\n*hello,4.955*\n*hello,4.955*')
      win = open('src.cpp.o.js').read()

      if '-O2' in self.emcc_args and not self.is_wasm():
        # Make sure ALLOW_MEMORY_GROWTH generates different code (should be less optimized)
        code_start = 'var TOTAL_MEMORY'
        fail = fail[fail.find(code_start):]
        win = win[win.find(code_start):]
        assert len(fail) < len(win), 'failing code - without memory growth on - is more optimized, and smaller' + str([len(fail), len(win)])

    test()

    if not self.is_wasm():
      print('split memory')
      self.set_setting('SPLIT_MEMORY', 16 * 1024 * 1024)
      test()
      self.set_setting('SPLIT_MEMORY', 0)

  def test_memorygrowth_3(self):
    # checks handling of malloc failure properly
    self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=0', '-s', 'ABORTING_MALLOC=0', '-s', 'SAFE_HEAP=1']
    self.do_run_in_out_file_test('tests', 'core', 'test_memorygrowth_3')

  def test_memorygrowth_wasm_mem_max(self):
    if not self.is_wasm():
      self.skipTest('wasm memory specific test')
    # check that memory growth does not exceed the wasm mem max limit
    self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=1', '-s', 'TOTAL_MEMORY=64Mb', '-s', 'WASM_MEM_MAX=100Mb']
    self.do_run_in_out_file_test('tests', 'core', 'test_memorygrowth_wasm_mem_max')

  def test_memorygrowth_3_force_fail_reallocBuffer(self):
    self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=1', '-DFAIL_REALLOC_BUFFER']
    self.do_run_in_out_file_test('tests', 'core', 'test_memorygrowth_3')

  def test_ssr(self): # struct self-ref
      src = '''
        #include <stdio.h>

        // see related things in openjpeg
        typedef struct opj_mqc_state {
          unsigned int qeval;
          int mps;
          struct opj_mqc_state *nmps;
          struct opj_mqc_state *nlps;
        } opj_mqc_state_t;

        static opj_mqc_state_t mqc_states[4] = {
          {0x5600, 0, &mqc_states[2], &mqc_states[3]},
          {0x5602, 1, &mqc_states[3], &mqc_states[2]},
        };

        int main() {
          printf("*%d*\\n", (int)(mqc_states+1)-(int)mqc_states);
          for (int i = 0; i < 2; i++)
            printf("%d:%d,%d,%d,%d\\n", i, mqc_states[i].qeval, mqc_states[i].mps,
                   (int)mqc_states[i].nmps-(int)mqc_states, (int)mqc_states[i].nlps-(int)mqc_states);
          return 0;
        }
        '''
      self.do_run(src, '''*16*\n0:22016,0,32,48\n1:22018,1,48,32\n''')

  def test_tinyfuncstr(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_tinyfuncstr')

  def test_llvmswitch(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_llvmswitch')

  # By default, when user has not specified a -std flag, Emscripten should always build .cpp files using the C++03 standard,
  # i.e. as if "-std=c++03" had been passed on the command line. On Linux with Clang 3.2 this is the case, but on Windows
  # with Clang 3.2 -std=c++11 has been chosen as default, because of
  # < jrose> clb: it's deliberate, with the idea that for people who don't care about the standard, they should be using the "best" thing we can offer on that platform
  def test_cxx03_do_run(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_cxx03_do_run')

  @no_emterpreter
  def test_bigswitch(self):
    src = open(path_from_root('tests', 'bigswitch.cpp')).read()
    self.do_run(src, '''34962: GL_ARRAY_BUFFER (0x8892)
26214: what?
35040: GL_STREAM_DRAW (0x88E0)
3060: what?
''', args=['34962', '26214', '35040', str(0xbf4)])

  @no_emterpreter
  def test_biggerswitch(self):
    num_cases = 20000
    switch_case = run_process([PYTHON, path_from_root('tests', 'gen_large_switchcase.py'), str(num_cases)], stdout=PIPE, stderr=PIPE).stdout
    self.do_run(switch_case, '''58996: 589965899658996
59297: 592975929759297
59598: default
59899: 598995989959899
Success!''')

  @no_wasm_backend('no implementation of computed gotos')
  def test_indirectbr(self):
      Building.COMPILER_TEST_OPTS = [x for x in Building.COMPILER_TEST_OPTS if x != '-g']

      self.do_run_in_out_file_test('tests', 'core', 'test_indirectbr')

  @no_wasm_backend('no implementation of computed gotos')
  def test_indirectbr_many(self):
      self.do_run_in_out_file_test('tests', 'core', 'test_indirectbr_many')

  def test_pack(self):
      src = '''
        #include <stdio.h>
        #include <string.h>

        #pragma pack(push,1)
        typedef struct header
        {
            unsigned char  id;
            unsigned short colour;
            unsigned char  desc;
        } header;
        #pragma pack(pop)

        typedef struct fatheader
        {
            unsigned char  id;
            unsigned short colour;
            unsigned char  desc;
        } fatheader;

        int main( int argc, const char *argv[] ) {
          header h, *ph = 0;
          fatheader fh, *pfh = 0;
          printf("*%d,%d,%d*\\n", sizeof(header), (int)((int)&h.desc - (int)&h.id), (int)(&ph[1])-(int)(&ph[0]));
          printf("*%d,%d,%d*\\n", sizeof(fatheader), (int)((int)&fh.desc - (int)&fh.id), (int)(&pfh[1])-(int)(&pfh[0]));
          return 0;
        }
        '''
      self.do_run(src, '*4,3,4*\n*6,4,6*')

  def test_varargs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_varargs')

  @no_wasm_backend('Calling varargs across function calls is undefined behavior in C,'
                   ' and asmjs and wasm implement it differently.')
  def test_varargs_multi(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_varargs_multi')

  @unittest.skip('clang cannot compile this code with that target yet')
  def test_varargs_byval(self):
    src = r'''
      #include <stdio.h>
      #include <stdarg.h>

      typedef struct type_a {
        union {
          double f;
          void *p;
          int i;
          short sym;
        } value;
      } type_a;

      enum mrb_vtype {
        MRB_TT_FALSE = 0,   /*   0 */
        MRB_TT_CLASS = 9    /*   9 */
      };

      typedef struct type_b {
        enum mrb_vtype tt:8;
      } type_b;

      void print_type_a(int argc, ...);
      void print_type_b(int argc, ...);

      int main(int argc, char *argv[])
      {
        type_a a;
        type_b b;
        a.value.p = (void*) 0x12345678;
        b.tt = MRB_TT_CLASS;

        printf("The original address of a is: %p\n", a.value.p);
        printf("The original type of b is: %d\n", b.tt);

        print_type_a(1, a);
        print_type_b(1, b);

        return 0;
      }

      void print_type_a(int argc, ...) {
        va_list ap;
        type_a a;

        va_start(ap, argc);
        a = va_arg(ap, type_a);
        va_end(ap);

        printf("The current address of a is: %p\n", a.value.p);
      }

      void print_type_b(int argc, ...) {
        va_list ap;
        type_b b;

        va_start(ap, argc);
        b = va_arg(ap, type_b);
        va_end(ap);

        printf("The current type of b is: %d\n", b.tt);
      }
      '''
    self.do_run(src, '''The original address of a is: 0x12345678
The original type of b is: 9
The current address of a is: 0x12345678
The current type of b is: 9
''')

  def test_functionpointer_libfunc_varargs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_functionpointer_libfunc_varargs')

  def test_structbyval(self):
    self.set_setting('INLINING_LIMIT', 50)

    # part 1: make sure that normally, passing structs by value works

    src = r'''
      #include <stdio.h>

      struct point
      {
        int x, y;
      };

      void dump(struct point p) {
        p.x++; // should not modify
        p.y++; // anything in the caller!
        printf("dump: %d,%d\n", p.x, p.y);
      }

      void dumpmod(struct point *p) {
        p->x++; // should not modify
        p->y++; // anything in the caller!
        printf("dump: %d,%d\n", p->x, p->y);
      }

      int main( int argc, const char *argv[] ) {
        point p = { 54, 2 };
        printf("pre:  %d,%d\n", p.x, p.y);
        dump(p);
        void (*dp)(point p) = dump; // And, as a function pointer
        dp(p);
        printf("post: %d,%d\n", p.x, p.y);
        dumpmod(&p);
        dumpmod(&p);
        printf("last: %d,%d\n", p.x, p.y);
        return 0;
      }
    '''
    self.do_run(src, 'pre:  54,2\ndump: 55,3\ndump: 55,3\npost: 54,2\ndump: 55,3\ndump: 56,4\nlast: 56,4')

    # Check for lack of warning in the generated code (they should appear in part 2)
    generated = open(os.path.join(self.get_dir(), 'src.cpp.o.js')).read()
    assert 'Casting a function pointer type to another with a different number of arguments.' not in generated, 'Unexpected warning'

    # part 2: make sure we warn about mixing c and c++ calling conventions here

    if self.emcc_args != []:
      # Optimized code is missing the warning comments
      return

    header = r'''
      struct point
      {
        int x, y;
      };

    '''
    open(os.path.join(self.get_dir(), 'header.h'), 'w').write(header)

    supp = r'''
      #include <stdio.h>
      #include "header.h"

      void dump(struct point p) {
        p.x++; // should not modify
        p.y++; // anything in the caller!
        printf("dump: %d,%d\n", p.x, p.y);
      }
    '''
    supp_name = os.path.join(self.get_dir(), 'supp.c')
    open(supp_name, 'w').write(supp)

    main = r'''
      #include <stdio.h>
      #include "header.h"

      #ifdef __cplusplus
      extern "C" {
      #endif
        void dump(struct point p);
      #ifdef __cplusplus
      }
      #endif

      int main( int argc, const char *argv[] ) {
        struct point p = { 54, 2 };
        printf("pre:  %d,%d\n", p.x, p.y);
        dump(p);
        void (*dp)(struct point p) = dump; // And, as a function pointer
        dp(p);
        printf("post: %d,%d\n", p.x, p.y);
        return 0;
      }
    '''
    main_name = os.path.join(self.get_dir(), 'main.cpp')
    open(main_name, 'w').write(main)

    Building.emcc(supp_name)
    Building.emcc(main_name)
    all_name = os.path.join(self.get_dir(), 'all.bc')
    Building.link([supp_name + '.o', main_name + '.o'], all_name)

    # This will fail! See explanation near the warning we check for, in the compiler source code
    run_process([PYTHON, EMCC, all_name] + self.emcc_args, check=False, stderr=PIPE)

    # Check for warning in the generated code
    generated = open(os.path.join(self.get_dir(), 'src.cpp.o.js')).read()
    print('skipping C/C++ conventions warning check, since not i386-pc-linux-gnu', file=sys.stderr)

  def test_stdlibs(self):
    # safe heap prints a warning that messes up our output.
    self.set_setting('SAFE_HEAP', 0)
    # needs atexit
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_stdlibs')

  def test_stdbool(self):
    src = r'''
        #include <stdio.h>
        #include <stdbool.h>

        int main() {
          bool x = true;
          bool y = false;
          printf("*%d*\n", x != y);
          return 0;
        }
      '''

    self.do_run(src, '*1*', force_c=True)

  def test_strtoll_hex(self):
    # tests strtoll for hex strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtoll_hex')

  def test_strtoll_dec(self):
    # tests strtoll for decimal strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtoll_dec')

  def test_strtoll_bin(self):
    # tests strtoll for binary strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtoll_bin')

  def test_strtoll_oct(self):
    # tests strtoll for decimal strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtoll_oct')

  def test_strtol_hex(self):
    # tests strtoll for hex strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtol_hex')

  def test_strtol_dec(self):
    # tests strtoll for decimal strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtol_dec')

  def test_strtol_bin(self):
    # tests strtoll for binary strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtol_bin')

  def test_strtol_oct(self):
    # tests strtoll for decimal strings (0x...)
    self.do_run_in_out_file_test('tests', 'core', 'test_strtol_oct')

  def test_atexit(self):
    # Confirms they are called in reverse order
    # needs atexits
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_atexit')

  def test_pthread_specific(self):
    src = open(path_from_root('tests', 'pthread', 'specific.c'), 'r').read()
    expected = open(path_from_root('tests', 'pthread', 'specific.c.txt'), 'r').read()
    self.do_run(src, expected, force_c=True)

  def test_pthread_equal(self):
    self.do_run_in_out_file_test('tests', 'pthread', 'test_pthread_equal')

  def test_tcgetattr(self):
    src = open(path_from_root('tests', 'termios', 'test_tcgetattr.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_time(self):
    src = open(path_from_root('tests', 'time', 'src.cpp'), 'r').read()
    expected = open(path_from_root('tests', 'time', 'output.txt'), 'r').read()
    self.do_run(src, expected)
    if 'TZ' in os.environ:
      print('TZ set in environment, skipping extra time zone checks')
    else:
      try:
        for tz in ['EST+05EDT', 'UTC+0']:
          print('extra tz test:', tz)
          # Run the test with different time zone settings if
          # possible. It seems that the TZ environment variable does not
          # work all the time (at least it's not well respected by
          # Node.js on Windows), but it does no harm either.
          os.environ['TZ'] = tz
          self.do_run(src, expected)
      finally:
        del os.environ['TZ']

  def test_timeb(self):
    # Confirms they are called in reverse order
    self.do_run_in_out_file_test('tests', 'core', 'test_timeb')

  def test_time_c(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_time_c')

  def test_gmtime(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_gmtime')

  def test_strptime_tm(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strptime_tm')

  def test_strptime_days(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strptime_days')

  def test_strptime_reentrant(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_strptime_reentrant')

  def test_strftime(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strftime')

  @no_wasm_backend("wasm backend doesn't compile intentional segfault into an abort() call. "
                   "It also doesn't segfault.")
  def test_intentional_fault(self):
    # Some programs intentionally segfault themselves, we should compile that into a throw
    src = open(path_from_root('tests', 'core', 'test_intentional_fault.c'), 'r').read()
    self.do_run(src, 'abort()' if self.run_name != 'asm2g' else 'abort("segmentation fault')

  def test_trickystring(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_trickystring')

  def test_statics(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_statics')

  def test_copyop(self):
    # clang generated code is vulnerable to this, as it uses
    # memcpy for assignments, with hardcoded numbers of bytes
    # (llvm-gcc copies items one by one). See QUANTUM_SIZE in
    # settings.js.
    test_path = path_from_root('tests', 'core', 'test_copyop')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output)

  def test_memcpy_memcmp(self):
    self.banned_js_engines = [V8_ENGINE] # Currently broken under V8_ENGINE but not node
    test_path = path_from_root('tests', 'core', 'test_memcpy_memcmp')
    src, output = (test_path + s for s in ('.c', '.out'))

    def check(result, err):
      result = result.replace('\n \n', '\n') # remove extra node output
      return hashlib.sha1(result.encode('utf-8')).hexdigest()

    self.do_run_from_file(src, output, output_nicerizer=check)

  def test_memcpy2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_memcpy2')

  def test_memcpy3(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_memcpy3')

  def test_memcpy_alignment(self):
    self.do_run(open(path_from_root('tests', 'test_memcpy_alignment.cpp'), 'r').read(), 'OK.')

  def test_memset_alignment(self):
    self.do_run(open(path_from_root('tests', 'test_memset_alignment.cpp'), 'r').read(), 'OK.')

  def test_memset(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_memset')

  def test_getopt(self):
    test_path = path_from_root('tests', 'core', 'test_getopt')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output, args=['-t', '12', '-n', 'foobar'])

  def test_getopt_long(self):
    test_path = path_from_root('tests', 'core', 'test_getopt_long')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output, args=['--file', 'foobar', '-b'])

  def test_memmove(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_memmove')

  def test_memmove2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_memmove2')

  def test_memmove3(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_memmove3')

  def test_flexarray_struct(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_flexarray_struct')

  def test_bsearch(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_bsearch')

  @no_wasm_backend("wasm backend has no support for fastcomp's -emscripten-assertions flag")
  def test_stack_overflow(self):
    self.set_setting('ASSERTIONS', 1)
    self.do_run(open(path_from_root('tests', 'core', 'stack_overflow.cpp')).read(), 'Stack overflow!')

  def test_stackAlloc(self):
    self.do_run_in_out_file_test('tests', 'core', 'stackAlloc')

  def test_nestedstructs(self):
      src = '''
        #include <stdio.h>
        #include "emscripten.h"

        struct base {
          int x;
          float y;
          union {
            int a;
            float b;
          };
          char c;
        };

        struct hashtableentry {
          int key;
          base data;
        };

        struct hashset {
          typedef hashtableentry entry;
          struct chain { entry elem; chain *next; };
        //  struct chainchunk { chain chains[100]; chainchunk *next; };
        };

        struct hashtable : hashset {
          hashtable() {
            base *b = NULL;
            entry *e = NULL;
            chain *c = NULL;
            printf("*%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d,%d|%d,%d,%d,%d,%d,%d,%d,%d,%d,%d*\\n",
              sizeof(base),
              int(&(b->x)), int(&(b->y)), int(&(b->a)), int(&(b->b)), int(&(b->c)),
              sizeof(hashtableentry),
              int(&(e->key)), int(&(e->data)), int(&(e->data.x)), int(&(e->data.y)), int(&(e->data.a)), int(&(e->data.b)), int(&(e->data.c)),
              sizeof(hashset::chain),
              int(&(c->elem)), int(&(c->next)), int(&(c->elem.key)), int(&(c->elem.data)), int(&(c->elem.data.x)), int(&(c->elem.data.y)), int(&(c->elem.data.a)), int(&(c->elem.data.b)), int(&(c->elem.data.c))
            );
          }
        };

        struct B { char buffer[62]; int last; char laster; char laster2; };

        struct Bits {
          unsigned short A : 1;
          unsigned short B : 1;
          unsigned short C : 1;
          unsigned short D : 1;
          unsigned short x1 : 1;
          unsigned short x2 : 1;
          unsigned short x3 : 1;
          unsigned short x4 : 1;
        };

        int main() {
          hashtable t;

          // Part 2 - the char[] should be compressed, BUT have a padding space at the end so the next
          // one is aligned properly. Also handle char; char; etc. properly.
          B *b = NULL;
          printf("*%d,%d,%d,%d,%d,%d,%d,%d,%d*\\n", int(b), int(&(b->buffer)), int(&(b->buffer[0])), int(&(b->buffer[1])), int(&(b->buffer[2])),
                                                    int(&(b->last)), int(&(b->laster)), int(&(b->laster2)), sizeof(B));

          // Part 3 - bitfields, and small structures
          Bits *b2 = NULL;
          printf("*%d*\\n", sizeof(Bits));

          return 0;
        }
        '''
      # Bloated memory; same layout as C/C++
      self.do_run(src, '*16,0,4,8,8,12|20,0,4,4,8,12,12,16|24,0,20,0,4,4,8,12,12,16*\n*0,0,0,1,2,64,68,69,72*\n*2*')

  @unittest.skip('BUILD_AS_SHARED_LIB=2 is deprecated')
  def test_runtimelink(self):
    if Building.LLVM_OPTS:
      self.skipTest('LLVM opts will optimize printf into puts in the parent, and the child will still look for puts')
    if self.get_setting('ASM_JS'):
      self.skipTest('asm does not support runtime linking')

    main, supp = self.setup_runtimelink_test()

    self.banned_js_engines = [NODE_JS] # node's global scope behaves differently than everything else, needs investigation FIXME
    self.set_setting('LINKABLE', 1)
    self.set_setting('BUILD_AS_SHARED_LIB', 2)

    self.build(supp, self.get_dir(), self.in_dir('supp.cpp'))
    shutil.move(self.in_dir('supp.cpp.o.js'), self.in_dir('liblib.so'))
    self.set_setting('BUILD_AS_SHARED_LIB', 0)

    self.set_setting('RUNTIME_LINKED_LIBS', ['liblib.so'])
    self.do_run(main, 'supp: 54,2\nmain: 56\nsupp see: 543\nmain see: 76\nok.')

  def prep_dlfcn_lib(self):
    self.set_setting('MAIN_MODULE', 0)
    self.set_setting('SIDE_MODULE', 1)

  def prep_dlfcn_main(self):
    self.set_setting('MAIN_MODULE', 1)
    self.set_setting('SIDE_MODULE', 0)

    with open('lib_so_pre.js', 'w') as f:
      f.write('''
    if (!Module['preRun']) Module['preRun'] = [];
    Module['preRun'].push(function() { FS.createDataFile('/', 'liblib.so', %s, true, false, false); });
''' % str(list(bytearray(open('liblib.so', 'rb').read()))))
    self.emcc_args += ['--pre-js', 'lib_so_pre.js']

  def build_dlfcn_lib(self, lib_src, dirname, filename):
    if self.get_setting('WASM'):
      # emcc emits a wasm in this case
      self.build(lib_src, dirname, filename, js_outfile=False)
      shutil.move(filename + '.o.wasm', os.path.join(dirname, 'liblib.so'))
    else:
      self.build(lib_src, dirname, filename)
      shutil.move(filename + '.o.js', os.path.join(dirname, 'liblib.so'))

  @needs_dlfcn
  def test_dlfcn_missing(self):
    self.set_setting('MAIN_MODULE', 1)
    src = r'''
      #include <dlfcn.h>
      #include <stdio.h>
      #include <assert.h>

      int main() {
        void* lib_handle = dlopen("libfoo.so", RTLD_NOW);
        assert(!lib_handle);
        printf("error: %s\n", dlerror());
        return 0;
      }
      '''
    self.do_run(src, 'error: Could not find dynamic lib: libfoo.so\n')

  @needs_dlfcn
  def test_dlfcn_basic(self):
    self.prep_dlfcn_lib()
    lib_src = '''
      #include <cstdio>

      class Foo {
      public:
        Foo() {
          puts("Constructing lib object.");
        }
      };

      Foo global;
      '''
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.cpp')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = '''
      #include <cstdio>
      #include <dlfcn.h>

      class Bar {
      public:
        Bar() {
          puts("Constructing main object.");
        }
      };

      Bar global;

      int main() {
        dlopen("liblib.so", RTLD_NOW);
        return 0;
      }
      '''
    self.do_run(src, 'Constructing main object.\nConstructing lib object.\n')

  @needs_dlfcn
  def test_dlfcn_i64(self):
    # avoid using asm2wasm imports, which don't work in side modules yet (should they?)
    self.set_setting('BINARYEN_TRAP_MODE', 'clamp')

    self.prep_dlfcn_lib()
    self.set_setting('EXPORTED_FUNCTIONS', ['_foo'])
    lib_src = '''
      int foo(int x) {
        return (long long)x / (long long)1234;
      }
      '''
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    self.set_setting('EXPORTED_FUNCTIONS', ['_main'])
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <dlfcn.h>

      typedef int (*intfunc)(int);

      void *p;

      int main() {
        p = malloc(1024);
        void *lib_handle = dlopen("liblib.so", 0);
        if (!lib_handle) {
          puts(dlerror());
          abort();
        }
        printf("load %p\n", lib_handle);
        intfunc x = (intfunc)dlsym(lib_handle, "foo");
        printf("foo func %p\n", x);
        if (p == 0) return 1;
        printf("|%d|\n", x(81234567));
        return 0;
      }
      '''
    self.do_run(src, '|65830|')

  @no_wasm # TODO: EM_ASM in shared wasm modules, stored inside the wasm somehow
  @needs_dlfcn
  def test_dlfcn_em_asm(self):
    self.prep_dlfcn_lib()
    lib_src = '''
      #include <emscripten.h>
      class Foo {
      public:
        Foo() {
          EM_ASM( out("Constructing lib object.") );
        }
      };
      Foo global;
      '''
    filename = 'liblib.cpp'
    self.build_dlfcn_lib(lib_src, self.get_dir(), filename)

    self.prep_dlfcn_main()
    src = '''
      #include <emscripten.h>
      #include <dlfcn.h>
      class Bar {
      public:
        Bar() {
          EM_ASM( out("Constructing main object.") );
        }
      };
      Bar global;
      int main() {
        dlopen("liblib.so", RTLD_NOW);
        EM_ASM( out("All done.") );
        return 0;
      }
      '''
    self.do_run(src, 'Constructing main object.\nConstructing lib object.\nAll done.\n')

  @needs_dlfcn
  def test_dlfcn_qsort(self):
    self.prep_dlfcn_lib()
    self.set_setting('EXPORTED_FUNCTIONS', ['_get_cmp'])
    lib_src = '''
      int lib_cmp(const void* left, const void* right) {
        const int* a = (const int*) left;
        const int* b = (const int*) right;
        if(*a > *b) return 1;
        else if(*a == *b) return  0;
        else return -1;
      }

      typedef int (*CMP_TYPE)(const void*, const void*);

      extern "C" CMP_TYPE get_cmp() {
        return lib_cmp;
      }
      '''
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.cpp')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc'])
    src = '''
      #include <stdio.h>
      #include <stdlib.h>
      #include <dlfcn.h>

      typedef int (*CMP_TYPE)(const void*, const void*);

      int main_cmp(const void* left, const void* right) {
        const int* a = (const int*) left;
        const int* b = (const int*) right;
        if(*a < *b) return 1;
        else if(*a == *b) return  0;
        else return -1;
      }

      int main() {
        void* lib_handle;
        CMP_TYPE (*getter_ptr)();
        CMP_TYPE lib_cmp_ptr;
        int arr[5] = {4, 2, 5, 1, 3};

        qsort((void*)arr, 5, sizeof(int), main_cmp);
        printf("Sort with main comparison: ");
        for (int i = 0; i < 5; i++) {
          printf("%d ", arr[i]);
        }
        printf("\\n");

        lib_handle = dlopen("liblib.so", RTLD_NOW);
        if (lib_handle == NULL) {
          printf("Could not load lib.\\n");
          return 1;
        }
        getter_ptr = (CMP_TYPE (*)()) dlsym(lib_handle, "get_cmp");
        if (getter_ptr == NULL) {
          printf("Could not find func.\\n");
          return 1;
        }
        lib_cmp_ptr = getter_ptr();
        qsort((void*)arr, 5, sizeof(int), lib_cmp_ptr);
        printf("Sort with lib comparison: ");
        for (int i = 0; i < 5; i++) {
          printf("%d ", arr[i]);
        }
        printf("\\n");

        return 0;
      }
      '''
    self.do_run(src, 'Sort with main comparison: 5 4 3 2 1 *Sort with lib comparison: 1 2 3 4 5 *',
                output_nicerizer=lambda x, err: x.replace('\n', '*'))

    if self.get_setting('ASM_JS') and SPIDERMONKEY_ENGINE and os.path.exists(SPIDERMONKEY_ENGINE[0]) and not self.is_wasm():
      out = run_js('liblib.so', engine=SPIDERMONKEY_ENGINE, full_output=True, stderr=STDOUT)
      if 'asm' in out:
        self.validate_asmjs(out)

  @needs_dlfcn
  def test_dlfcn_data_and_fptr(self):
    # Failing under v8 since: https://chromium-review.googlesource.com/712595
    if self.is_wasm():
      self.banned_js_engines = [V8_ENGINE]

    if Building.LLVM_OPTS:
      self.skipTest('LLVM opts will optimize out parent_func')

    self.prep_dlfcn_lib()
    lib_src = '''
      #include <stdio.h>

      int global = 42;

      extern void parent_func(); // a function that is defined in the parent

      void lib_fptr() {
        printf("Second calling lib_fptr from main.\\n");
        parent_func();
        // call it also through a pointer, to check indexizing
        void (*p_f)();
        p_f = parent_func;
        p_f();
      }

      extern "C" void (*func(int x, void(*fptr)()))() {
        printf("In func: %d\\n", x);
        fptr();
        return lib_fptr;
      }
      '''
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.cpp')
    self.set_setting('EXPORTED_FUNCTIONS', ['_func'])
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    self.set_setting('LINKABLE', 1)
    src = '''
      #include <stdio.h>
      #include <dlfcn.h>
      #include <emscripten.h>

      typedef void (*FUNCTYPE(int, void(*)()))();

      FUNCTYPE func;

      void EMSCRIPTEN_KEEPALIVE parent_func() {
        printf("parent_func called from child\\n");
      }

      void main_fptr() {
        printf("First calling main_fptr from lib.\\n");
      }

      int main() {
        void* lib_handle;
        FUNCTYPE* func_fptr;

        // Test basic lib loading.
        lib_handle = dlopen("liblib.so", RTLD_NOW);
        if (lib_handle == NULL) {
          printf("Could not load lib.\\n");
          return 1;
        }

        // Test looked up function.
        func_fptr = (FUNCTYPE*) dlsym(lib_handle, "func");
        // Load twice to test cache.
        func_fptr = (FUNCTYPE*) dlsym(lib_handle, "func");
        if (func_fptr == NULL) {
          printf("Could not find func.\\n");
          return 1;
        }

        // Test passing function pointers across module bounds.
        void (*fptr)() = func_fptr(13, main_fptr);
        fptr();

        // Test global data.
        int* global = (int*) dlsym(lib_handle, "global");
        if (global == NULL) {
          printf("Could not find global.\\n");
          return 1;
        }

        printf("Var: %d\\n", *global);

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main'])
    self.do_run(src, 'In func: 13*First calling main_fptr from lib.*Second calling lib_fptr from main.*parent_func called from child*parent_func called from child*Var: 42*',
                output_nicerizer=lambda x, err: x.replace('\n', '*'))

  @needs_dlfcn
  def test_dlfcn_varargs(self):
    # this test is not actually valid - it fails natively. the child should fail to be loaded, not load and successfully see the parent print_ints func
    self.set_setting('LINKABLE', 1)

    self.prep_dlfcn_lib()
    lib_src = r'''
      void print_ints(int n, ...);
      extern "C" void func() {
        print_ints(2, 13, 42);
      }
      '''
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.cpp')
    self.set_setting('EXPORTED_FUNCTIONS', ['_func'])
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = r'''
      #include <stdarg.h>
      #include <stdio.h>
      #include <dlfcn.h>
      #include <assert.h>

      void print_ints(int n, ...) {
        va_list args;
        va_start(args, n);
        for (int i = 0; i < n; i++) {
          printf("%d\n", va_arg(args, int));
        }
        va_end(args);
      }

      int main() {
        void* lib_handle;
        void (*fptr)();

        print_ints(2, 100, 200);

        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle);
        fptr = (void (*)())dlsym(lib_handle, "func");
        fptr();

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main'])
    self.do_run(src, '100\n200\n13\n42\n')

  @needs_dlfcn
  def test_dlfcn_alignment_and_zeroing(self):
    self.prep_dlfcn_lib()
    self.set_setting('TOTAL_MEMORY', 16 * 1024 * 1024)
    lib_src = r'''
      extern "C" {
        int prezero = 0;
        __attribute__((aligned(1024))) int superAligned = 12345;
        int postzero = 0;
      }
      '''
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.cpp')
    self.build_dlfcn_lib(lib_src, dirname, filename)
    for i in range(10):
      curr = '%d.so' % i
      shutil.copyfile('liblib.so', curr)
      self.emcc_args += ['--embed-file', curr]

    self.prep_dlfcn_main()
    self.set_setting('TOTAL_MEMORY', 128 * 1024 * 1024)
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <string.h>
      #include <dlfcn.h>
      #include <assert.h>
      #include <emscripten.h>

      int main() {
        printf("'prepare' memory with non-zero inited stuff\n");
        int num = 120 * 1024 * 1024; // total is 128; we'll use 5*5 = 25 at least, so allocate pretty much all of it
        void* mem = malloc(num);
        assert(mem);
        printf("setting this range to non-zero: %d - %d\n", int(mem), int(mem) + num);
        memset(mem, 1, num);
        EM_ASM({
          var value = HEAP8[64*1024*1024];
          out('verify middle of memory is non-zero: ' + value);
          assert(value === 1);
        });
        free(mem);
        for (int i = 0; i < 10; i++) {
          char* curr = "?.so";
          curr[0] = '0' + i;
          printf("loading %s\n", curr);
          void* lib_handle = dlopen(curr, RTLD_NOW);
          if (!lib_handle) {
            puts(dlerror());
            assert(0);
          }
          printf("getting superAligned\n");
          int* superAligned = (int*)dlsym(lib_handle, "superAligned");
          assert(superAligned);
          assert(int(superAligned) % 1024 == 0); // alignment
          printf("checking value of superAligned, at %d\n", superAligned);
          assert(*superAligned == 12345); // value
          printf("getting prezero\n");
          int* prezero = (int*)dlsym(lib_handle, "prezero");
          assert(prezero);
          printf("checking value of prezero, at %d\n", prezero);
          assert(*prezero == 0);
          *prezero = 1;
          assert(*prezero != 0);
          printf("getting postzero\n");
          int* postzero = (int*)dlsym(lib_handle, "postzero");
          printf("checking value of postzero, at %d\n", postzero);
          assert(postzero);
          printf("checking value of postzero\n");
          assert(*postzero == 0);
          *postzero = 1;
          assert(*postzero != 0);
        }
        printf("success.\n");
        return 0;
      }
      '''
    self.do_run(src, 'success.\n')

  @no_wasm # TODO: this needs to add JS functions to a wasm Table, need to figure that out
  @needs_dlfcn
  def test_dlfcn_self(self):
    self.prep_dlfcn_main()

    def post(filename):
      with open(filename) as f:
        for line in f:
          if 'var NAMED_GLOBALS' in line:
            table = line
            break
        else:
          raise Exception('Could not find symbol table!')
      table = table[table.find('{'):table.find('}') + 1]
      # ensure there aren't too many globals; we don't want unnamed_addr
      assert table.count(',') <= 30, table.count(',')

    test_path = path_from_root('tests', 'core', 'test_dlfcn_self')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output, post_build=post)

  @needs_dlfcn
  def test_dlfcn_unique_sig(self):
    self.prep_dlfcn_lib()
    lib_src = '''
      #include <stdio.h>

      int myfunc(int a, int b, int c, int d, int e, int f, int g, int h, int i, int j, int k, int l, int m) {
        return 13;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_myfunc'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = '''
      #include <assert.h>
      #include <stdio.h>
      #include <dlfcn.h>

      typedef int (*FUNCTYPE)(int, int, int, int, int, int, int, int, int, int, int, int, int);

      int main() {
        void *lib_handle;
        FUNCTYPE func_ptr;

        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle != NULL);

        func_ptr = (FUNCTYPE)dlsym(lib_handle, "myfunc");
        assert(func_ptr != NULL);
        assert(func_ptr(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) == 13);

        puts("success");

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc'])
    self.do_run(src, 'success', force_c=True)

  @needs_dlfcn
  def test_dlfcn_info(self):

    self.prep_dlfcn_lib()
    lib_src = '''
      #include <stdio.h>

      int myfunc(int a, int b, int c, int d, int e, int f, int g, int h, int i, int j, int k, int l, int m) {
        return 13;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_myfunc'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = '''
      #include <assert.h>
      #include <stdio.h>
      #include <string.h>
      #include <dlfcn.h>

      typedef int (*FUNCTYPE)(int, int, int, int, int, int, int, int, int, int, int, int, int);

      int main() {
        void *lib_handle;
        FUNCTYPE func_ptr;

        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle != NULL);

        func_ptr = (FUNCTYPE)dlsym(lib_handle, "myfunc");
        assert(func_ptr != NULL);
        assert(func_ptr(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) == 13);

        /* Verify that we don't corrupt func_ptr when calling dladdr.  */
        Dl_info info;
        memset(&info, 0, sizeof(info));
        dladdr(func_ptr, &info);

        assert(func_ptr != NULL);
        assert(func_ptr(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) == 13);

        /* Verify something useful lives in info.  */
        assert(info.dli_fname != NULL);
        assert(info.dli_fbase == NULL);
        assert(info.dli_sname == NULL);
        assert(info.dli_saddr == NULL);

        puts("success");

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc'])
    self.do_run(src, 'success', force_c=True)

  @needs_dlfcn
  def test_dlfcn_stacks(self):
    self.prep_dlfcn_lib()
    lib_src = '''
      #include <assert.h>
      #include <stdio.h>
      #include <string.h>

      int myfunc(const char *input) {
        char bigstack[1024] = { 0 };

        // make sure we didn't just trample the stack!
        assert(!strcmp(input, "foobar"));

        snprintf(bigstack, sizeof(bigstack), input);
        return strlen(bigstack);
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_myfunc'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = '''
      #include <assert.h>
      #include <stdio.h>
      #include <dlfcn.h>
      #include <string.h>

      typedef int (*FUNCTYPE)(const char *);

      int main() {
        void *lib_handle;
        FUNCTYPE func_ptr;
        char str[128];

        snprintf(str, sizeof(str), "foobar");

        // HACK: Use strcmp in the main executable so that it doesn't get optimized out and the dynamic library
        //       is able to use it.
        assert(!strcmp(str, "foobar"));

        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle != NULL);

        func_ptr = (FUNCTYPE)dlsym(lib_handle, "myfunc");
        assert(func_ptr != NULL);
        assert(func_ptr(str) == 6);

        puts("success");

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc', '_strcmp'])
    self.do_run(src, 'success', force_c=True)

  @needs_dlfcn
  def test_dlfcn_funcs(self):
    self.prep_dlfcn_lib()
    lib_src = r'''
      #include <assert.h>
      #include <stdio.h>
      #include <string.h>

      typedef void (*voidfunc)();
      typedef void (*intfunc)(int);

      void callvoid(voidfunc f) { f(); }
      void callint(voidfunc f, int x) { f(x); }

      void void_0() { printf("void 0\n"); }
      void void_1() { printf("void 1\n"); }
      voidfunc getvoid(int i) {
        switch(i) {
          case 0: return void_0;
          case 1: return void_1;
          default: return NULL;
        }
      }

      void int_0(int x) { printf("int 0 %d\n", x); }
      void int_1(int x) { printf("int 1 %d\n", x); }
      intfunc getint(int i) {
        switch(i) {
          case 0: return int_0;
          case 1: return int_1;
          default: return NULL;
        }
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_callvoid', '_callint', '_getvoid', '_getint'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = r'''
      #include <assert.h>
      #include <stdio.h>
      #include <dlfcn.h>

      typedef void (*voidfunc)();
      typedef void (*intfunc)(int);

      typedef void (*voidcaller)(voidfunc);
      typedef void (*intcaller)(intfunc, int);

      typedef voidfunc (*voidgetter)(int);
      typedef intfunc (*intgetter)(int);

      void void_main() { printf("main.\n"); }
      void int_main(int x) { printf("main %d\n", x); }

      int main() {
        printf("go\n");
        void *lib_handle;
        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle != NULL);

        voidcaller callvoid = (voidcaller)dlsym(lib_handle, "callvoid");
        assert(callvoid != NULL);
        callvoid(void_main);

        intcaller callint = (intcaller)dlsym(lib_handle, "callint");
        assert(callint != NULL);
        callint(int_main, 201);

        voidgetter getvoid = (voidgetter)dlsym(lib_handle, "getvoid");
        assert(getvoid != NULL);
        callvoid(getvoid(0));
        callvoid(getvoid(1));

        intgetter getint = (intgetter)dlsym(lib_handle, "getint");
        assert(getint != NULL);
        callint(getint(0), 54);
        callint(getint(1), 9000);

        assert(getint(1000) == NULL);

        puts("ok");
        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc'])
    self.do_run(src, '''go
main.
main 201
void 0
void 1
int 0 54
int 1 9000
ok
''', force_c=True)

  @needs_dlfcn
  def test_dlfcn_mallocs(self):
    # will be exhausted without functional malloc/free
    self.set_setting('TOTAL_MEMORY', 64 * 1024 * 1024)

    self.prep_dlfcn_lib()
    lib_src = r'''
      #include <assert.h>
      #include <stdio.h>
      #include <string.h>
      #include <stdlib.h>

      void *mallocproxy(int n) { return malloc(n); }
      void freeproxy(void *p) { free(p); }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_mallocproxy', '_freeproxy'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = open(path_from_root('tests', 'dlmalloc_proxy.c')).read()
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc', '_free'])
    self.do_run(src, '''*294,153*''', force_c=True)

  @needs_dlfcn
  def test_dlfcn_longjmp(self):
    self.prep_dlfcn_lib()
    lib_src = r'''
      #include <setjmp.h>
      #include <stdio.h>

      void jumpy(jmp_buf buf) {
        static int i = 0;
        i++;
        if (i == 10) longjmp(buf, i);
        printf("pre %d\n", i);
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_jumpy'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.c')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = r'''
      #include <assert.h>
      #include <stdio.h>
      #include <dlfcn.h>
      #include <setjmp.h>

      typedef void (*jumpfunc)(jmp_buf);

      int main() {
        printf("go!\n");

        void *lib_handle;
        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle != NULL);

        jumpfunc jumpy = (jumpfunc)dlsym(lib_handle, "jumpy");
        assert(jumpy);

        jmp_buf buf;
        int jmpval = setjmp(buf);
        if (jmpval == 0) {
          while (1) jumpy(buf);
        } else {
          printf("out!\n");
        }

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc', '_free'])
    self.do_run(src, '''go!
pre 1
pre 2
pre 3
pre 4
pre 5
pre 6
pre 7
pre 8
pre 9
out!
''', force_c=True)

  @needs_dlfcn
  def zzztest_dlfcn_exceptions(self): # TODO: make this work. need to forward tempRet0 across modules
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)

    self.prep_dlfcn_lib()
    lib_src = r'''
      extern "C" {
      int ok() {
        return 65;
      }
      int fail() {
        throw 123;
      }
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_ok', '_fail'])
    dirname = self.get_dir()
    filename = os.path.join(dirname, 'liblib.cpp')
    self.build_dlfcn_lib(lib_src, dirname, filename)

    self.prep_dlfcn_main()
    src = r'''
      #include <assert.h>
      #include <stdio.h>
      #include <dlfcn.h>

      typedef int (*intfunc)();

      int main() {
        printf("go!\n");

        void *lib_handle;
        lib_handle = dlopen("liblib.so", RTLD_NOW);
        assert(lib_handle != NULL);

        intfunc okk = (intfunc)dlsym(lib_handle, "ok");
        intfunc faill = (intfunc)dlsym(lib_handle, "fail");
        assert(okk && faill);

        try {
          printf("ok: %d\n", okk());
        } catch(...) {
          printf("wha\n");
        }

        try {
          printf("fail: %d\n", faill());
        } catch(int x) {
          printf("int %d\n", x);
        }

        try {
          printf("fail: %d\n", faill());
        } catch(double x) {
          printf("caught %f\n", x);
        }

        return 0;
      }
      '''
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc', '_free'])
    self.do_run(src, '''go!
ok: 65
int 123
ok
''')

  def dylink_test(self, main, side, expected, header=None, main_emcc_args=[], force_c=False, need_reverse=True, auto_load=True):
    if header:
      open('header.h', 'w').write(header)

    emcc_args = self.emcc_args[:]
    try:
      # side settings
      self.set_setting('MAIN_MODULE', 0)
      self.set_setting('SIDE_MODULE', 1)
      side_suffix = 'js' if not self.is_wasm() else 'wasm'
      if isinstance(side, list):
        # side is just a library
        try_delete('liblib.cpp.o.' + side_suffix)
        run_process([PYTHON, EMCC] + side + self.emcc_args + self.serialize_settings() + ['-o', os.path.join(self.get_dir(), 'liblib.cpp.o.' + side_suffix)])
      else:
        base = 'liblib.cpp' if not force_c else 'liblib.c'
        try_delete(base + '.o.' + side_suffix)
        self.build(side, self.get_dir(), base, js_outfile=(side_suffix == 'js'))
        if force_c:
          shutil.move(base + '.o.' + side_suffix, 'liblib.cpp.o.' + side_suffix)
      if SPIDERMONKEY_ENGINE and os.path.exists(SPIDERMONKEY_ENGINE[0]) and not self.is_wasm():
        out = run_js('liblib.cpp.o.js', engine=SPIDERMONKEY_ENGINE, full_output=True, stderr=STDOUT)
        if 'asm' in out:
          self.validate_asmjs(out)
      shutil.move('liblib.cpp.o.' + side_suffix, 'liblib.so')

      # main settings
      self.set_setting('MAIN_MODULE', 1)
      self.set_setting('SIDE_MODULE', 0)
      if auto_load:
        open('pre.js', 'w').write('''
Module = {
  dynamicLibraries: ['liblib.so'],
};
  ''')
        self.emcc_args += ['--pre-js', 'pre.js'] + main_emcc_args

      if isinstance(main, list):
        # main is just a library
        try_delete('src.cpp.o.js')
        run_process([PYTHON, EMCC] + main + self.emcc_args + self.serialize_settings() + ['-o', os.path.join(self.get_dir(), 'src.cpp.o.js')])
        self.do_run(None, expected, no_build=True)
      else:
        self.do_run(main, expected, force_c=force_c)
    finally:
      self.emcc_args = emcc_args[:]

    if need_reverse:
      # test the reverse as well
      print('flip')
      self.dylink_test(side, main, expected, header, main_emcc_args, force_c, need_reverse=False)

  @needs_dlfcn
  def test_dylink_basics(self):
    def test():
      self.dylink_test('''
        #include <stdio.h>
        extern int sidey();
        int main() {
          printf("other says %d.\\n", sidey());
          return 0;
        }
      ''', '''
        int sidey() { return 11; }
      ''', 'other says 11.')
    test()

    if self.is_wasm():
      print('test memory growth with dynamic linking, which works in wasm')
      self.set_setting('ALLOW_MEMORY_GROWTH', 1)
      test()

  @needs_dlfcn
  def test_dylink_floats(self):
    self.dylink_test('''
      #include <stdio.h>
      extern float sidey();
      int main() {
        printf("other says %.2f.\\n", sidey()+1);
        return 0;
      }
    ''', '''
      float sidey() { return 11.5; }
    ''', 'other says 12.50')

  @needs_dlfcn
  def test_dylink_printfs(self):
    self.dylink_test(r'''
      #include <stdio.h>
      extern void sidey();
      int main() {
        printf("hello from main\n");
        sidey();
        return 0;
      }
    ''', r'''
      #include <stdio.h>
      void sidey() { printf("hello from side\n"); }
    ''', 'hello from main\nhello from side\n')

  @needs_dlfcn
  def test_dylink_funcpointer(self):
    self.dylink_test(r'''
      #include <stdio.h>
      #include "header.h"
      voidfunc sidey(voidfunc f);
      void a() { printf("hello from funcptr\n"); }
      int main() {
        sidey(a)();
        return 0;
      }
    ''', '''
      #include "header.h"
      voidfunc sidey(voidfunc f) { return f; }
    ''', 'hello from funcptr\n', header='typedef void (*voidfunc)();')

  @needs_dlfcn
  def test_dylink_funcpointers(self):
    self.dylink_test(r'''
      #include <stdio.h>
      #include "header.h"
      int sidey(voidfunc f);
      void areturn0() { printf("hello 0\n"); }
      void areturn1() { printf("hello 1\n"); }
      void areturn2() { printf("hello 2\n"); }
      int main(int argc, char **argv) {
        voidfunc table[3] = { areturn0, areturn1, areturn2 };
        table[sidey(NULL)]();
        return 0;
      }
    ''', '''
      #include "header.h"
      int sidey(voidfunc f) { if (f) f(); return 1; }
    ''', 'hello 1\n', header='typedef void (*voidfunc)();')

  @no_wasm # uses function tables in an asm.js specific way
  @needs_dlfcn
  def test_dylink_funcpointers2(self):
    self.dylink_test(r'''
      #include "header.h"
      #include <emscripten.h>
      void left1() { printf("left1\n"); }
      void left2() { printf("left2\n"); }
      voidfunc getleft1() { return left1; }
      voidfunc getleft2() { return left2; }
      int main(int argc, char **argv) {
        printf("main\n");
        EM_ASM({
          // make the function table sizes a non-power-of-two
          alignFunctionTables();
          Module['FUNCTION_TABLE_v'].push(0, 0, 0, 0, 0);
          var newSize = alignFunctionTables();
          //out('new size of function tables: ' + newSize);
          // when masked, the two function pointers 1 and 2 should not happen to fall back to the right place
          assert(((newSize+1) & 3) !== 1 || ((newSize+2) & 3) !== 2);
          loadDynamicLibrary('liblib.so');
        });
        volatilevoidfunc f;
        f = (volatilevoidfunc)left1;
        f();
        f = (volatilevoidfunc)left2;
        f();
        f = (volatilevoidfunc)getright1();
        f();
        f = (volatilevoidfunc)getright2();
        f();
        second();
        return 0;
      }
    ''', r'''
      #include "header.h"
      void right1() { printf("right1\n"); }
      void right2() { printf("right2\n"); }
      voidfunc getright1() { return right1; }
      voidfunc getright2() { return right2; }
      void second() {
        printf("second\n");
        volatilevoidfunc f;
        f = (volatilevoidfunc)getleft1();
        f();
        f = (volatilevoidfunc)getleft2();
        f();
        f = (volatilevoidfunc)right1;
        f();
        f = (volatilevoidfunc)right2;
        f();
      }
    ''', 'main\nleft1\nleft2\nright1\nright2\nsecond\nleft1\nleft2\nright1\nright2\n', header='''
      #include <stdio.h>
      typedef void (*voidfunc)();
      typedef volatile voidfunc volatilevoidfunc;
      voidfunc getleft1();
      voidfunc getleft2();
      voidfunc getright1();
      voidfunc getright2();
      void second();
    ''', need_reverse=False, auto_load=False)

  @needs_dlfcn
  def test_dylink_funcpointers_wrapper(self):
    self.dylink_test(r'''
      #include <stdio.h>
      #include "header.h"
      int main(int argc, char **argv) {
        volatile charfunc f = emscripten_run_script;
        f("out('one')");
        f = get();
        f("out('two')");
        return 0;
      }
    ''', '''
      #include "header.h"
      charfunc get() {
        return emscripten_run_script;
      }
    ''', 'one\ntwo\n', header='''
      #include <emscripten.h>
      typedef void (*charfunc)(const char*);
      extern charfunc get();
    ''')

  @needs_dlfcn
  def test_dylink_funcpointers_float(self):
    # avoid using asm2wasm imports, which don't work in side modules yet (should they?)
    self.set_setting('BINARYEN_TRAP_MODE', 'clamp')
    self.dylink_test(r'''
      #include <stdio.h>
      #include "header.h"
      int sidey(floatfunc f);
      float areturn0(float f) { printf("hello 0: %f\n", f); return 0; }
      float areturn1(float f) { printf("hello 1: %f\n", f); return 1; }
      float areturn2(float f) { printf("hello 2: %f\n", f); return 2; }
      int main(int argc, char **argv) {
        volatile floatfunc table[3] = { areturn0, areturn1, areturn2 };
        printf("got: %d\n", (int)table[sidey(NULL)](12.34));
        return 0;
      }
    ''', '''
      #include "header.h"
      int sidey(floatfunc f) { if (f) f(56.78); return 1; }
    ''', 'hello 1: 12.340000\ngot: 1\n', header='typedef float (*floatfunc)(float);')

  @needs_dlfcn
  def test_dylink_global_init(self):
    self.dylink_test(r'''
      #include <stdio.h>
      struct Class {
        Class() { printf("a new Class\n"); }
      };
      static Class c;
      int main() {
        return 0;
      }
    ''', r'''
      void nothing() {}
    ''', 'a new Class\n')

  @needs_dlfcn
  def test_dylink_global_inits(self):
    def test():
      self.dylink_test(header=r'''
        #include <stdio.h>
        struct Class {
          Class(const char *name) { printf("new %s\n", name); }
        };
      ''', main=r'''
        #include "header.h"
        static Class c("main");
        int main() {
          return 0;
        }
      ''', side=r'''
        #include "header.h"
        static Class c("side");
      ''', expected=['new main\nnew side\n', 'new side\nnew main\n'])
    test()

    # TODO: this in wasm
    if self.get_setting('ASSERTIONS') == 1 and not self.is_wasm():
      print('check warnings')
      self.set_setting('ASSERTIONS', 2)
      test()
      full = run_js('src.cpp.o.js', engine=JS_ENGINES[0], full_output=True, stderr=STDOUT)
      self.assertNotContained("trying to dynamically load symbol '__ZN5ClassC2EPKc' (from 'liblib.so') that already exists", full)

  @needs_dlfcn
  def test_dylink_i64(self):
    self.dylink_test('''
      #include <stdio.h>
      #include <stdint.h>
      extern int64_t sidey();
      int main() {
        printf("other says %llx.\\n", sidey());
        return 0;
      }
    ''', '''
      #include <stdint.h>
      int64_t sidey() {
        volatile int64_t x = 11;
        x = x * x * x * x;
        x += x % 17;
        x += (x * (1 << 30));
        x -= 96;
        x = (x + 1000) / ((x % 5) + 1);
        volatile uint64_t y = x / 2;
        x = y / 3;
        y = y * y * y * y;
        y += y % 17;
        y += (y * (1 << 30));
        y -= 121;
        y = (y + 1000) / ((y % 5) + 1);
        x += y;
        return x;
      }
    ''', 'other says 175a1ddee82b8c31.')

  @needs_dlfcn
  def test_dylink_i64_b(self):
    self.dylink_test(r'''
      #include <stdio.h>
      #include <stdint.h>
      extern int64_t sidey();
      int main() {
        printf("other says %lld.\n", sidey());
        return 0;
      }
    ''', '''
      #include <stdint.h>
      int64_t sidey() {
        volatile int64_t x = 0x12345678abcdef12LL;
        x += x % 17;
        x = 18 - x;
        return x;
      }
    ''', 'other says -1311768467750121224.')

  @needs_dlfcn
  def test_dylink_class(self):
    self.dylink_test(header=r'''
      #include <stdio.h>
      struct Class {
        Class(const char *name);
      };
    ''', main=r'''
      #include "header.h"
      int main() {
        Class c("main");
        return 0;
      }
    ''', side=r'''
      #include "header.h"
      Class::Class(const char *name) { printf("new %s\n", name); }
    ''', expected=['new main\n'])

  @needs_dlfcn
  def test_dylink_global_var(self):
    self.dylink_test(main=r'''
      #include <stdio.h>
      extern int x;
      int main() {
        printf("extern is %d.\n", x);
        return 0;
      }
    ''', side=r'''
      int x = 123;
    ''', expected=['extern is 123.\n'])

  @needs_dlfcn
  def test_dylink_global_var_modded(self):
    self.dylink_test(main=r'''
      #include <stdio.h>
      extern int x;
      int main() {
        printf("extern is %d.\n", x);
        return 0;
      }
    ''', side=r'''
      int x = 123;
      struct Initter {
        Initter() { x = 456; }
      };
      Initter initter;
    ''', expected=['extern is 456.\n'])

  @needs_dlfcn
  def test_dylink_stdlib(self):
    self.dylink_test(header=r'''
      #include <math.h>
      #include <stdlib.h>
      #include <string.h>
      char *side(const char *data);
      double pow_two(double x);
    ''', main=r'''
      #include <stdio.h>
      #include "header.h"
      int main() {
        char *temp = side("hello through side\n");
        char *ret = (char*)malloc(strlen(temp)+1);
        strcpy(ret, temp);
        temp[1] = 'x';
        puts(ret);
        printf("pow_two: %d.\n", int(pow_two(5.9)));
        return 0;
      }
    ''', side=r'''
      #include "header.h"
      char *side(const char *data) {
        char *ret = (char*)malloc(strlen(data)+1);
        strcpy(ret, data);
        return ret;
      }
      double pow_two(double x) {
        return pow(2, x);
      }
    ''', expected=['hello through side\n\npow_two: 59.'])

  @needs_dlfcn
  def test_dylink_jslib(self):
    # avoid using asm2wasm imports, which don't work in side modules yet (should they?)
    self.set_setting('BINARYEN_TRAP_MODE', 'clamp')
    open('lib.js', 'w').write(r'''
      mergeInto(LibraryManager.library, {
        test_lib_func: function(x) {
          return x + 17.2;
        }
      });
    ''')
    self.dylink_test(header=r'''
      extern "C" { extern double test_lib_func(int input); }
    ''', main=r'''
      #include <stdio.h>
      #include "header.h"
      extern double sidey();
      int main2() { return 11; }
      int main() {
        int input = sidey();
        double temp = test_lib_func(input);
        printf("other says %.2f\n", temp);
        printf("more: %.5f, %d\n", temp, input);
        return 0;
      }
    ''', side=r'''
      #include <stdio.h>
      #include "header.h"
      extern int main2();
      double sidey() {
        int temp = main2();
        printf("main2 sed: %d\n", temp);
        printf("main2 sed: %u, %c\n", temp, temp/2);
        return test_lib_func(temp);
      }
    ''', expected='other says 45.2', main_emcc_args=['--js-library', 'lib.js'])

  @needs_dlfcn
  def test_dylink_global_var_jslib(self):
    open('lib.js', 'w').write(r'''
      mergeInto(LibraryManager.library, {
        jslib_x: 'allocate(1, "i32*", ALLOC_STATIC)',
        jslib_x__postset: 'HEAP32[_jslib_x>>2] = 148;',
      });
    ''')
    self.dylink_test(main=r'''
      #include <stdio.h>
      extern "C" int jslib_x;
      extern void call_side();
      int main() {
        printf("main: jslib_x is %d.\n", jslib_x);
        call_side();
        return 0;
      }
    ''', side=r'''
      #include <stdio.h>
      extern "C" int jslib_x;
      void call_side() {
        printf("side: jslib_x is %d.\n", jslib_x);
      }
    ''', expected=['main: jslib_x is 148.\nside: jslib_x is 148.\n'], main_emcc_args=['--js-library', 'lib.js'])

  @needs_dlfcn
  def test_dylink_many_postSets(self):
    NUM = 1234
    self.dylink_test(header=r'''
      #include <stdio.h>
      typedef void (*voidfunc)();
      static void simple() {
        printf("simple.\n");
      }
      static volatile voidfunc funcs[''' + str(NUM) + '] = { ' + ','.join(['simple'] * NUM) + r''' };
      static void test() {
        volatile int i = ''' + str(NUM - 1) + r''';
        funcs[i]();
        i = 0;
        funcs[i]();
      }
      extern void more();
    ''', main=r'''
      #include "header.h"
      int main() {
        test();
        more();
        return 0;
      }
    ''', side=r'''
      #include "header.h"
      void more() {
        test();
      }
    ''', expected=['simple.\nsimple.\nsimple.\nsimple.\n'])

  @needs_dlfcn
  def test_dylink_postSets_chunking(self):
    self.dylink_test(header=r'''
      extern int global_var;
    ''', main=r'''
      #include <stdio.h>
      #include "header.h"

      // prepare 99 global variable with local initializer
      static int p = 1;
      #define P(x) __attribute__((used)) int *padding##x = &p;
      P(01) P(02) P(03) P(04) P(05) P(06) P(07) P(08) P(09) P(10)
      P(11) P(12) P(13) P(14) P(15) P(16) P(17) P(18) P(19) P(20)
      P(21) P(22) P(23) P(24) P(25) P(26) P(27) P(28) P(29) P(30)
      P(31) P(32) P(33) P(34) P(35) P(36) P(37) P(38) P(39) P(40)
      P(41) P(42) P(43) P(44) P(45) P(46) P(47) P(48) P(49) P(50)
      P(51) P(52) P(53) P(54) P(55) P(56) P(57) P(58) P(59) P(60)
      P(61) P(62) P(63) P(64) P(65) P(66) P(67) P(68) P(69) P(70)
      P(71) P(72) P(73) P(74) P(75) P(76) P(77) P(78) P(79) P(80)
      P(81) P(82) P(83) P(84) P(85) P(86) P(87) P(88) P(89) P(90)
      P(91) P(92) P(93) P(94) P(95) P(96) P(97) P(98) P(99)

      // prepare global variable with global initializer
      int *ptr = &global_var;

      int main(int argc, char *argv[]) {
        printf("%d\n", *ptr);
      }
    ''', side=r'''
      #include "header.h"

      int global_var = 12345;
    ''', expected=['12345\n'])

  @no_wasm # todo
  @needs_dlfcn
  def test_dylink_syslibs(self): # one module uses libcxx, need to force its inclusion when it isn't the main
    def test(syslibs, expect_pass=True, need_reverse=True):
      print('syslibs', syslibs, self.get_setting('ASSERTIONS'))
      passed = True
      try:
        os.environ['EMCC_FORCE_STDLIBS'] = syslibs
        self.dylink_test(main=r'''
          void side();
          int main() {
            side();
            return 0;
          }
        ''', side=r'''
          #include <iostream>
          void side() { std::cout << "cout hello from side\n"; }
        ''', expected=['cout hello from side\n'], need_reverse=need_reverse)
      except Exception as e:
        if expect_pass:
          raise e
        print('(seeing expected fail)')
        passed = False
        assertion = 'build the MAIN_MODULE with EMCC_FORCE_STDLIBS=1 in the environment'
        if self.get_setting('ASSERTIONS'):
          self.assertContained(assertion, str(e))
        else:
          self.assertNotContained(assertion, str(e))
      finally:
        del os.environ['EMCC_FORCE_STDLIBS']
      assert passed == expect_pass, ['saw', passed, 'but expected', expect_pass]

    test('libcxx')
    test('1')
    if 'ASSERTIONS=1' not in self.emcc_args:
      self.set_setting('ASSERTIONS', 0)
      test('', expect_pass=False, need_reverse=False)
    else:
      print('(skip ASSERTIONS == 0 part)')
    self.set_setting('ASSERTIONS', 1)
    test('', expect_pass=False, need_reverse=False)

  @needs_dlfcn
  def test_dylink_iostream(self):
    try:
      os.environ['EMCC_FORCE_STDLIBS'] = 'libcxx'
      self.dylink_test(header=r'''
        #include <iostream>
        #include <string>
        std::string side();
      ''', main=r'''
        #include "header.h"
        int main() {
          std::cout << "hello from main " << side() << std::endl;
          return 0;
        }
      ''', side=r'''
        #include "header.h"
        std::string side() { return "and hello from side"; }
      ''', expected=['hello from main and hello from side\n'])
    finally:
      del os.environ['EMCC_FORCE_STDLIBS']

  @needs_dlfcn
  def test_dylink_dynamic_cast(self): # issue 3465
    self.dylink_test(header=r'''
      class Base {
      public:
          virtual void printName();
      };

      class Derived : public Base {
      public:
          void printName();
      };
    ''', main=r'''
      #include "header.h"
      #include <iostream>

      using namespace std;

      int main() {
        cout << "starting main" << endl;

        Base *base = new Base();
        Base *derived = new Derived();
        base->printName();
        derived->printName();

        if (dynamic_cast<Derived*>(derived)) {
          cout << "OK" << endl;
        } else {
          cout << "KO" << endl;
        }

        return 0;
      }
    ''', side=r'''
      #include "header.h"
      #include <iostream>

      using namespace std;

      void Base::printName() {
          cout << "Base" << endl;
      }

      void Derived::printName() {
          cout << "Derived" << endl;
      }
    ''', expected=['starting main\nBase\nDerived\nOK'])

  @needs_dlfcn
  def test_dylink_raii_exceptions(self):
    self.emcc_args += ['-s', 'DISABLE_EXCEPTION_CATCHING=0']

    self.dylink_test(main=r'''
      #include <stdio.h>
      extern int side();
      int main() {
        printf("from side: %d.\n", side());
      }
    ''', side=r'''
      #include <stdio.h>
      typedef int (*ifdi)(float, double, int);
      int func_with_special_sig(float a, double b, int c) {
        printf("special %f %f %d\n", a, b, c);
        return 1337;
      }
      struct DestructorCaller {
        ~DestructorCaller() { printf("destroy\n"); }
      };
      int side() {
        // d has a destructor that must be called on function
        // exit, which means an invoke will be used for the
        // indirect call here - and the signature of that call
        // is special and not present in the main module, so
        // it must be generated for the side module.
        DestructorCaller d;
        volatile ifdi p = func_with_special_sig;
        return p(2.18281, 3.14159, 42);
      }
    ''', expected=['special 2.182810 3.141590 42\ndestroy\nfrom side: 1337.\n'])

  @needs_dlfcn
  def test_dylink_hyper_dupe(self):
    dylib_suffix = '.js' if not self.is_wasm() else '.wasm'

    self.set_setting('TOTAL_MEMORY', 64 * 1024 * 1024)

    if self.get_setting('ASSERTIONS'):
      self.emcc_args += ['-s', 'ASSERTIONS=2']

    # test hyper-dynamic linking, and test duplicate warnings
    open('third.cpp', 'w').write(r'''
      #include <stdio.h>
      int sidef() { return 36; }
      int sideg = 49;
      int bsidef() { return 536; }
      extern void only_in_second_1(int x);
      extern int second_to_third;
      int third_to_second = 1337;
      void only_in_third_0() {
        // note we access our own globals directly, so
        // it doesn't matter that overriding failed
        printf("only_in_third_0: %d, %d, %d\n", sidef(), sideg, second_to_third);
        only_in_second_1(2112);
      }
      void only_in_third_1(int x) {
        printf("only_in_third_1: %d, %d, %d, %d\n", sidef(), sideg, second_to_third, x);
      }
    ''')
    run_process([PYTHON, EMCC, 'third.cpp', '-s', 'SIDE_MODULE=1'] + Building.COMPILER_TEST_OPTS + self.emcc_args + ['-o', 'third' + dylib_suffix])

    self.dylink_test(main=r'''
      #include <stdio.h>
      #include <emscripten.h>
      extern int sidef();
      extern int sideg;
      extern int bsidef();
      extern int bsideg;
      extern void only_in_second_0();
      extern void only_in_third_0();
      int main() {
        EM_ASM({
          loadDynamicLibrary('third%s'); // hyper-dynamic! works at least for functions (and consts not used in same block)
        });
        printf("sidef: %%d, sideg: %%d.\n", sidef(), sideg);
        printf("bsidef: %%d.\n", bsidef());
        only_in_second_0();
        only_in_third_0();
      }
    ''' % dylib_suffix,
                     side=r'''
      #include <stdio.h>
      int sidef() { return 10; } // third will try to override these, but fail!
      int sideg = 20;
      extern void only_in_third_1(int x);
      int second_to_third = 500;
      extern int third_to_second;
      void only_in_second_0() {
        printf("only_in_second_0: %d, %d, %d\n", sidef(), sideg, third_to_second);
        only_in_third_1(1221);
      }
      void only_in_second_1(int x) {
        printf("only_in_second_1: %d, %d, %d, %d\n", sidef(), sideg, third_to_second, x);
      }
    ''',
                     expected=['sidef: 10, sideg: 20.\nbsidef: 536.\nonly_in_second_0: 10, 20, 1337\nonly_in_third_1: 36, 49, 500, 1221\nonly_in_third_0: 36, 49, 500\nonly_in_second_1: 10, 20, 1337, 2112\n'],
                     need_reverse=not self.is_wasm()) # in wasm, we can't flip as the side would have an EM_ASM, which we don't support yet TODO

    if self.get_setting('ASSERTIONS'):
      print('check warnings')
      full = run_js('src.cpp.o.js', engine=JS_ENGINES[0], full_output=True, stderr=STDOUT)
      self.assertContained("warning: trying to dynamically load symbol '_sideg' (from 'third%s') that already exists" % dylib_suffix, full)

  @needs_dlfcn
  def test_dylink_dot_a(self):
    # .a linking must force all .o files inside it, when in a shared module
    open('third.cpp', 'w').write(r'''
      int sidef() { return 36; }
    ''')
    run_process([PYTHON, EMCC, 'third.cpp'] + Building.COMPILER_TEST_OPTS + self.emcc_args + ['-o', 'third.o', '-c'])

    open('fourth.cpp', 'w').write(r'''
      int sideg() { return 17; }
    ''')
    run_process([PYTHON, EMCC, 'fourth.cpp'] + Building.COMPILER_TEST_OPTS + self.emcc_args + ['-o', 'fourth.o', '-c'])

    run_process([PYTHON, EMAR, 'rc', 'libfourth.a', 'fourth.o'])

    self.dylink_test(main=r'''
      #include <stdio.h>
      #include <emscripten.h>
      extern int sidef();
      extern int sideg();
      int main() {
        printf("sidef: %d, sideg: %d.\n", sidef(), sideg());
      }
    ''',
                     side=['libfourth.a', 'third.o'], # contents of libtwo.a must be included, even if they aren't referred to!
                     expected=['sidef: 36, sideg: 17.\n'])

  @needs_dlfcn
  def test_dylink_spaghetti(self):
    self.dylink_test(main=r'''
      #include <stdio.h>
      int main_x = 72;
      extern int side_x;
      int adjust = side_x + 10;
      int *ptr = &side_x;
      struct Class {
        Class() {
          printf("main init sees %d, %d, %d.\n", adjust, *ptr, main_x);
        }
      };
      Class cm;
      int main() {
        printf("main main sees %d, %d, %d.\n", adjust, *ptr, main_x);
        return 0;
      }
    ''', side=r'''
      #include <stdio.h>
      extern int main_x;
      int side_x = -534;
      int adjust2 = main_x + 10;
      int *ptr2 = &main_x;
      struct Class {
        Class() {
          printf("side init sees %d, %d, %d.\n", adjust2, *ptr2, side_x);
        }
      };
      Class cs;
    ''', expected=['side init sees 82, 72, -534.\nmain init sees -524, -534, 72.\nmain main sees -524, -534, 72.',
                   'main init sees -524, -534, 72.\nside init sees 82, 72, -534.\nmain main sees -524, -534, 72.'])

  @needs_dlfcn
  def test_dylink_zlib(self):
    # avoid using asm2wasm imports, which don't work in side modules yet (should they?)
    self.set_setting('BINARYEN_TRAP_MODE', 'clamp')
    Building.COMPILER_TEST_OPTS += ['-I' + path_from_root('tests', 'zlib')]

    run_process([PYTHON, path_from_root('embuilder.py'), 'build', 'zlib'])

    zlib = shared.Cache.get_path(os.path.join('ports-builds', 'zlib', 'libz.a'))
    side = [zlib]
    with env_modify({'EMCC_FORCE_STDLIBS': 'libcextra'}):
      self.dylink_test(main=open(path_from_root('tests', 'zlib', 'example.c'), 'r').read(),
                       side=side,
                       expected=open(path_from_root('tests', 'zlib', 'ref.txt'), 'r').read(),
                       force_c=True)

  # @needs_dlfcn
  # def test_dylink_bullet(self):
  #   Building.COMPILER_TEST_OPTS += ['-I' + path_from_root('tests', 'bullet', 'src')]
  #   side = get_bullet_library(self, True)
  #   self.dylink_test(main=open(path_from_root('tests', 'bullet', 'Demos', 'HelloWorld', 'HelloWorld.cpp'), 'r').read(),
  #                    side=side,
  #                    expected=[open(path_from_root('tests', 'bullet', 'output.txt'), 'r').read(), # different roundings
  #                              open(path_from_root('tests', 'bullet', 'output2.txt'), 'r').read(),
  #                              open(path_from_root('tests', 'bullet', 'output3.txt'), 'r').read()])

  def test_random(self):
    src = r'''#include <stdlib.h>
#include <stdio.h>

int main()
{
    srandom(0xdeadbeef);
    printf("%ld\n", random());
}
'''
    self.do_run(src, '956867869')

  def test_rand(self):
    src = r'''#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
int main()
{
    // we need RAND_MAX to be a bitmask (power of 2 minus 1). this assertions guarantees
    // if RAND_MAX changes the test failure will focus attention on that issue here.
    assert(RAND_MAX == 0x7fffffff);

    srand(0xdeadbeef);
    for(int i = 0; i < 10; ++i)
        printf("%d\n", rand());

    unsigned int seed = 0xdeadbeef;
    for(int i = 0; i < 10; ++i)
        printf("%d\n", rand_r(&seed));

    bool haveEvenAndOdd = true;
    for(int i = 1; i <= 30; ++i)
    {
        int mask = 1 << i;
        if (mask > RAND_MAX) break;
        bool haveEven = false;
        bool haveOdd = false;
        for(int j = 0; j < 1000 && (!haveEven || !haveOdd); ++j)
        {
            if ((rand() & mask) == 0)
                haveEven = true;
            else
                haveOdd = true;
        }
        haveEvenAndOdd = haveEvenAndOdd && haveEven && haveOdd;
    }
    if (haveEvenAndOdd)
        printf("Have even and odd!\n");

    return 0;
}
'''
    expected = '''490242850
2074599277
1480056542
1912638067
931112055
2110392489
2053422194
1614832492
216117595
174823244
760368382
602359081
1121118963
1291018924
1608306807
352705809
958258461
1182561381
114276303
1481323674
Have even and odd!
'''
    self.do_run(src, expected)

  def test_strtod(self):
    src = open(path_from_root('tests', 'core', 'test_strtod.c'), 'r').read()
    expected = open(path_from_root('tests', 'core', 'test_strtod.out'), 'r').read()
    self.do_run(src, expected)

  def test_strtold(self):
    if not self.is_wasm_backend():
      # XXX add real support for long double
      expected_file = 'test_strtod.out'
    else:
      expected_file = 'test_strtold.out'
    src = open(path_from_root('tests', 'core', 'test_strtold.c'), 'r').read()
    expected = open(path_from_root('tests', 'core', expected_file), 'r').read()
    self.do_run(src, expected)

  def test_strtok(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strtok')

  def test_parseInt(self):
    src = open(path_from_root('tests', 'parseInt', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'parseInt', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_transtrcase(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_transtrcase')

  def test_printf(self):
    self.banned_js_engines = [NODE_JS, V8_ENGINE] # SpiderMonkey and V8 do different things to float64 typed arrays, un-NaNing, etc.
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    src = open(path_from_root('tests', 'printf', 'test.c'), 'r').read()
    expected = open(path_from_root('tests', 'printf', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_printf_2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_printf_2')

  def test_printf_float(self):
    self.do_run_in_out_file_test('tests', 'printf', 'test_float')

  def test_printf_octal(self):
    self.do_run_in_out_file_test('tests', 'printf', 'test_octal')

  def test_vprintf(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_vprintf')

  def test_vsnprintf(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_vsnprintf')

  def test_printf_more(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_printf_more')

  def test_perrar(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_perrar')

  def test_atoX(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_atoX')

  def test_strstr(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strstr')

  def test_fnmatch(self):
    # Run one test without assertions, for additional coverage
    # assert 'asm2m' in core_test_modes
    if self.run_name == 'asm2m':
      i = self.emcc_args.index('ASSERTIONS=1')
      assert i > 0 and self.emcc_args[i - 1] == '-s'
      self.emcc_args[i] = 'ASSERTIONS=0'
      print('flip assertions off')
    self.do_run_in_out_file_test('tests', 'core', 'fnmatch')

  def test_sscanf(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf')

  def test_sscanf_2(self):
    # doubles
    for ftype in ['float', 'double']:
      src = r'''
          #include <stdio.h>

          int main(){
              char strval1[] = "1.2345678901";
              char strval2[] = "1.23456789e5";
              char strval3[] = "1.23456789E5";
              char strval4[] = "1.2345678e-5";
              char strval5[] = "1.2345678E-5";
              double dblval = 1.2345678901;
              double tstval;

              sscanf(strval1, "%lf", &tstval);
              if(dblval != tstval) printf("FAIL: Values are not equal: %lf %lf\n", dblval, tstval);
              else printf("Pass: %lf %lf\n", tstval, dblval);

              sscanf(strval2, "%lf", &tstval);
              dblval = 123456.789;
              if(dblval != tstval) printf("FAIL: Values are not equal: %lf %lf\n", dblval, tstval);
              else printf("Pass: %lf %lf\n", tstval, dblval);

              sscanf(strval3, "%lf", &tstval);
              dblval = 123456.789;
              if(dblval != tstval) printf("FAIL: Values are not equal: %lf %lf\n", dblval, tstval);
              else printf("Pass: %lf %lf\n", tstval, dblval);

              sscanf(strval4, "%lf", &tstval);
              dblval = 0.000012345678;
              if(dblval != tstval) printf("FAIL: Values are not equal: %lf %lf\n", dblval, tstval);
              else printf("Pass: %lf %lf\n", tstval, dblval);

              sscanf(strval5, "%lf", &tstval);
              dblval = 0.000012345678;
              if(dblval != tstval) printf("FAIL: Values are not equal: %lf %lf\n", dblval, tstval);
              else printf("Pass: %lf %lf\n", tstval, dblval);

              return 0;
          }
        '''
      if ftype == 'float':
        self.do_run(src.replace('%lf', '%f').replace('double', 'float'), '''Pass: 1.234568 1.234568
Pass: 123456.789062 123456.789062
Pass: 123456.789062 123456.789062
Pass: 0.000012 0.000012
Pass: 0.000012 0.000012''')
      else:
        self.do_run(src, '''Pass: 1.234568 1.234568
Pass: 123456.789000 123456.789000
Pass: 123456.789000 123456.789000
Pass: 0.000012 0.000012
Pass: 0.000012 0.000012''')

  def test_sscanf_n(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_n')

  def test_sscanf_whitespace(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_whitespace')

  def test_sscanf_other_whitespace(self):
    # use i16s in printf
    self.set_setting('SAFE_HEAP', 0)
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_other_whitespace')

  def test_sscanf_3(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_3')

  def test_sscanf_4(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_4')

  def test_sscanf_5(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_5')

  def test_sscanf_6(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_6')

  def test_sscanf_skip(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_skip')

  def test_sscanf_caps(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_caps')

  def test_sscanf_hex(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_hex')

  def test_sscanf_float(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_sscanf_float')

  def test_langinfo(self):
    src = open(path_from_root('tests', 'langinfo', 'test.c'), 'r').read()
    expected = open(path_from_root('tests', 'langinfo', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_files(self):
    self.banned_js_engines = [SPIDERMONKEY_ENGINE] # closure can generate variables called 'gc', which pick up js shell stuff
    if self.maybe_closure(): # Use closure here, to test we don't break FS stuff
      self.emcc_args = [x for x in self.emcc_args if x != '-g'] # ensure we test --closure 1 --memory-init-file 1 (-g would disable closure)
    elif '-O3' in self.emcc_args and not self.is_wasm():
      print('closure 2')
      self.emcc_args += ['--closure', '2'] # Use closure 2 here for some additional coverage

    self.emcc_args += ['-s', 'FORCE_FILESYSTEM=1']

    print('base', self.emcc_args)

    post = '''
def process(filename):
  src = \'\'\'
    Module = {
      'noFSInit': true,
      'preRun': function() {
        FS.createLazyFile('/', 'test.file', 'test.file', true, false);
        // Test FS_* exporting
        Module['FS_createDataFile']('/', 'somefile.binary', [100, 200, 50, 25, 10, 77, 123], true, false, false);  // 200 becomes -56, since signed chars are used in memory
        var test_files_input = 'hi there!';
        var test_files_input_index = 0;
        FS.init(function() {
          return test_files_input.charCodeAt(test_files_input_index++) || null;
        });
      }
    };
  \'\'\' + open(filename, 'r').read()
  open(filename, 'w').write(src)
'''
    other = open(os.path.join(self.get_dir(), 'test.file'), 'w')
    other.write('some data')
    other.close()

    src = open(path_from_root('tests', 'files.cpp'), 'r').read()

    mem_file = 'src.cpp.o.js.mem'
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1'], ['-s', 'SYSCALL_DEBUG=1']]:
      print(mode)
      self.emcc_args = orig_args + mode
      try_delete(mem_file)

      def clean(out, err):
        return '\n'.join([line for line in (out + err).split('\n') if 'binaryen' not in line and 'wasm' not in line and 'so not running' not in line])

      self.do_run(src, [x if 'SYSCALL_DEBUG=1' not in mode else ('syscall! 146,SYS_writev' if self.run_name == 'default' else 'syscall! 146') for x in ('size: 7\ndata: 100,-56,50,25,10,77,123\nloop: 100 -56 50 25 10 77 123 \ninput:hi there!\ntexto\n$\n5 : 10,30,20,11,88\nother=some data.\nseeked=me da.\nseeked=ata.\nseeked=ta.\nfscanfed: 10 - hello\n5 bytes to dev/null: 5\nok.\ntexte\n', 'size: 7\ndata: 100,-56,50,25,10,77,123\nloop: 100 -56 50 25 10 77 123 \ninput:hi there!\ntexto\ntexte\n$\n5 : 10,30,20,11,88\nother=some data.\nseeked=me da.\nseeked=ata.\nseeked=ta.\nfscanfed: 10 - hello\n5 bytes to dev/null: 5\nok.\n')],
                  js_transform=post, output_nicerizer=clean)
      if self.uses_memory_init_file():
        assert os.path.exists(mem_file), 'File %s does not exist' % mem_file

  def test_files_m(self):
    # Test for Module.stdin etc.
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)

    post = '''
def process(filename):
  src = \'\'\'
    Module = {
      data: [10, 20, 40, 30],
      stdin: function() { return Module.data.pop() || null },
      stdout: function(x) { out('got: ' + x) }
    };
  \'\'\' + open(filename, 'r').read()
  open(filename, 'w').write(src)
'''
    src = r'''
      #include <stdio.h>
      #include <unistd.h>

      int main () {
        char c;
        fprintf(stderr, "isatty? %d,%d,%d\n", isatty(fileno(stdin)), isatty(fileno(stdout)), isatty(fileno(stderr)));
        while ((c = fgetc(stdin)) != EOF) {
          putc(c+5, stdout);
        }
        return 0;
      }
      '''

    def clean(out, err):
      return '\n'.join([line for line in (out + err).split('\n') if 'warning' not in line and 'binaryen' not in line])

    self.do_run(src, ('got: 35\ngot: 45\ngot: 25\ngot: 15\n \nisatty? 0,0,1\n', 'got: 35\ngot: 45\ngot: 25\ngot: 15\nisatty? 0,0,1\n', 'isatty? 0,0,1\ngot: 35\ngot: 45\ngot: 25\ngot: 15\n'), js_transform=post, output_nicerizer=clean)

  def test_mount(self):
    self.set_setting('FORCE_FILESYSTEM', 1)
    src = open(path_from_root('tests', 'fs', 'test_mount.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_getdents64(self):
    src = open(path_from_root('tests', 'fs', 'test_getdents64.cpp'), 'r').read()
    self.do_run(src, '..')

  def test_getdents64_special_cases(self):
    Building.COMPILER_TEST_OPTS += ['-std=c++11']
    src = path_from_root('tests', 'fs', 'test_getdents64_special_cases.cpp')
    out = path_from_root('tests', 'fs', 'test_getdents64_special_cases.out')
    self.do_run_from_file(src, out, assert_identical=True)

  def test_getcwd_with_non_ascii_name(self):
    src = path_from_root('tests', 'fs', 'test_getcwd_with_non_ascii_name.cpp')
    out = path_from_root('tests', 'fs', 'test_getcwd_with_non_ascii_name.out')
    Building.COMPILER_TEST_OPTS += ['-std=c++11']
    self.do_run_from_file(src, out, assert_identical=True)

  def test_fwrite_0(self):
    test_path = path_from_root('tests', 'core', 'test_fwrite_0')
    src, output = (test_path + s for s in ('.c', '.out'))

    orig_args = self.emcc_args
    for mode in [[], ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1']]:
      self.emcc_args = orig_args + mode
      self.do_run_from_file(src, output)

  def test_fgetc_ungetc(self):
    print('TODO: update this test once the musl ungetc-on-EOF-stream bug is fixed upstream and reaches us')
    self.set_setting('SYSCALL_DEBUG', 1)
    self.clear()
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    for fs in ['MEMFS', 'NODEFS']:
      print(fs)
      src = open(path_from_root('tests', 'stdio', 'test_fgetc_ungetc.c'), 'r').read()
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run(src, 'success', force_c=True, js_engines=[NODE_JS])

  def test_fgetc_unsigned(self):
    src = r'''
      #include <stdio.h>
      int main() {
        FILE *file = fopen("file_with_byte_234.txt", "rb");
        int c = fgetc(file);
        printf("*%d\n", c);
      }
    '''
    open('file_with_byte_234.txt', 'wb').write(b'\xea')
    self.emcc_args += ['--embed-file', 'file_with_byte_234.txt']
    self.do_run(src, '*234\n')

  def test_fgets_eol(self):
    src = r'''
      #include <stdio.h>
      char buf[32];
      int main()
      {
        const char *r = "SUCCESS";
        FILE *f = fopen("eol.txt", "r");
        while (fgets(buf, 32, f) != NULL) {
          if (buf[0] == '\0') {
            r = "FAIL";
            break;
          }
        }
        printf("%s\n", r);
        fclose(f);
        return 0;
      }
    '''
    open('eol.txt', 'wb').write(b'\n')
    self.emcc_args += ['--embed-file', 'eol.txt']
    self.do_run(src, 'SUCCESS\n')

  def test_fscanf(self):
    open(os.path.join(self.get_dir(), 'three_numbers.txt'), 'w').write('''-1 0.1 -.1''')
    src = r'''
      #include <stdio.h>
      #include <assert.h>
      #include <float.h>
      int main()
      {
          float x = FLT_MAX, y = FLT_MAX, z = FLT_MAX;

          FILE* fp = fopen("three_numbers.txt", "r");
          if (fp) {
              int match = fscanf(fp, " %f %f %f ", &x, &y, &z);
              printf("match = %d\n", match);
              printf("x = %0.1f, y = %0.1f, z = %0.1f\n", x, y, z);
          } else {
              printf("failed to open three_numbers.txt\n");
          }
          return 0;
      }
    '''
    self.emcc_args += ['--embed-file', 'three_numbers.txt']
    self.do_run(src, 'match = 3\nx = -1.0, y = 0.1, z = -0.1\n')

  def test_fscanf_2(self):
    open('a.txt', 'w').write('''1/2/3 4/5/6 7/8/9
''')
    self.emcc_args += ['--embed-file', 'a.txt']
    self.do_run(r'''#include <cstdio>
#include <iostream>

using namespace std;

int
main( int argv, char ** argc ) {
    cout << "fscanf test" << endl;

    FILE * file;
    file = fopen("a.txt", "rb");
    int vertexIndex[4];
    int normalIndex[4];
    int uvIndex[4];

    int matches = fscanf(file, "%d/%d/%d %d/%d/%d %d/%d/%d %d/%d/%d\n", &vertexIndex[0], &uvIndex[0], &normalIndex[0], &vertexIndex    [1], &uvIndex[1], &normalIndex[1], &vertexIndex[2], &uvIndex[2], &normalIndex[2], &vertexIndex[3], &uvIndex[3], &normalIndex[3]);

    cout << matches << endl;

    return 0;
}
''', 'fscanf test\n9\n')

  def test_fileno(self):
    open(os.path.join(self.get_dir(), 'empty.txt'), 'w').write('')
    src = r'''
      #include <stdio.h>
      #include <unistd.h>
      int main()
      {
          FILE* fp = fopen("empty.txt", "r");
          if (fp) {
              printf("%d\n", fileno(fp));
          } else {
              printf("failed to open empty.txt\n");
          }
          return 0;
      }
    '''
    self.emcc_args += ['--embed-file', 'empty.txt']
    self.do_run(src, '3\n')

  def test_readdir(self):
    src = open(path_from_root('tests', 'dirent', 'test_readdir.c'), 'r').read()
    self.do_run(src, '''SIGILL: Illegal instruction
success
n: 8
name: tmp
name: proc
name: nocanread
name: home
name: foobar
name: dev
name: ..
name: .
''', force_c=True)

  def test_readdir_empty(self):
    src = open(path_from_root('tests', 'dirent', 'test_readdir_empty.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_stat(self):
    src = open(path_from_root('tests', 'stat', 'test_stat.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_stat_chmod(self):
    src = open(path_from_root('tests', 'stat', 'test_chmod.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_stat_mknod(self):
    src = open(path_from_root('tests', 'stat', 'test_mknod.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def add_pre_run(self, code):
    with open('pre.js', 'w') as f:
      f.write('Module.preRun = function() { %s }' % code)
    self.emcc_args += ['--pre-js', 'pre.js']

  def add_post_run(self, code):
    with open('pre.js', 'w') as f:
      f.write('Module.postRun = function() { %s }' % code)
    self.emcc_args += ['--pre-js', 'pre.js']

  def test_fcntl(self):
    self.add_pre_run("FS.createDataFile('/', 'test', 'abcdef', true, true, false);")
    src = open(path_from_root('tests', 'fcntl', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'fcntl', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_fcntl_open(self):
    src = open(path_from_root('tests', 'fcntl-open', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'fcntl-open', 'output.txt'), 'r').read()
    self.do_run(src, expected, force_c=True)

  def test_fcntl_misc(self):
    self.add_pre_run("FS.createDataFile('/', 'test', 'abcdef', true, true, false);")
    src = open(path_from_root('tests', 'fcntl-misc', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'fcntl-misc', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_poll(self):
    self.add_pre_run('''
      var dummy_device = FS.makedev(64, 0);
      FS.registerDevice(dummy_device, {});

      FS.createDataFile('/', 'file', 'abcdef', true, true, false);
      FS.mkdev('/device', dummy_device);
    ''')
    test_path = path_from_root('tests', 'core', 'test_poll')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  def test_statvfs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_statvfs')

  def test_libgen(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_libgen')

  def test_utime(self):
    src = open(path_from_root('tests', 'utime', 'test_utime.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_utf(self):
    self.banned_js_engines = [SPIDERMONKEY_ENGINE] # only node handles utf well
    self.set_setting('EXPORTED_FUNCTIONS', ['_main', '_malloc'])
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['getValue', 'setValue', 'UTF8ToString', 'stringToUTF8'])
    self.do_run_in_out_file_test('tests', 'core', 'test_utf')

  def test_utf32(self):
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['UTF32ToString', 'stringToUTF32', 'lengthBytesUTF32'])
    self.do_run(open(path_from_root('tests', 'utf32.cpp')).read(), 'OK.')
    self.do_run(open(path_from_root('tests', 'utf32.cpp')).read(), 'OK.', args=['-fshort-wchar'])

  def test_utf8(self):
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS',
                     ['UTF8ToString', 'stringToUTF8', 'AsciiToString', 'stringToAscii'])
    Building.COMPILER_TEST_OPTS += ['-std=c++11']
    self.do_run(open(path_from_root('tests', 'utf8.cpp')).read(), 'OK.')

  def test_utf8_textdecoder(self):
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['UTF8ToString', 'stringToUTF8'])
    Building.COMPILER_TEST_OPTS += ['--embed-file', path_from_root('tests/utf8_corpus.txt') + '@/utf8_corpus.txt']
    self.do_run(open(path_from_root('tests', 'benchmark_utf8.cpp')).read(), 'OK.')

  def test_utf16_textdecoder(self):
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['UTF16ToString', 'stringToUTF16', 'lengthBytesUTF16'])
    Building.COMPILER_TEST_OPTS += ['--embed-file', path_from_root('tests/utf16_corpus.txt') + '@/utf16_corpus.txt']
    self.do_run(open(path_from_root('tests', 'benchmark_utf16.cpp')).read(), 'OK.')

  @no_wasm_backend('printf is incorrectly handling float values')
  def test_wprintf(self):
    test_path = path_from_root('tests', 'core', 'test_wprintf')
    src, output = (test_path + s for s in ('.cpp', '.out'))
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1']]:
      self.emcc_args = orig_args + mode
      self.do_run_from_file(src, output)

  def test_direct_string_constant_usage(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_direct_string_constant_usage')

  def test_std_cout_new(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_std_cout_new')

  def test_istream(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    test_path = path_from_root('tests', 'core', 'test_istream')
    src, output = (test_path + s for s in ('.c', '.out'))

    for linkable in [0]: # , 1]:
      print(linkable)
      # regression check for issue #273
      self.set_setting('LINKABLE', linkable)
      self.do_run_from_file(src, output)

  def test_fs_base(self):
    # TODO(sbc): It seems that INCLUDE_FULL_LIBRARY will generally generate
    # undefined symbols at link time so perhaps have it imply this setting?
    self.set_setting('WARN_ON_UNDEFINED_SYMBOLS', 0)
    self.set_setting('INCLUDE_FULL_LIBRARY', 1)
    self.add_pre_run(open(path_from_root('tests', 'filesystem', 'src.js'), 'r').read())
    src = 'int main() {return 0;}\n'
    expected = open(path_from_root('tests', 'filesystem', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  @also_with_noderawfs
  def test_fs_nodefs_rw(self, js_engines=[NODE_JS]):
    self.set_setting('SYSCALL_DEBUG', 1)
    src = open(path_from_root('tests', 'fs', 'test_nodefs_rw.c'), 'r').read()
    self.do_run(src, 'success', force_c=True, js_engines=js_engines)
    print('closure')
    self.emcc_args += ['--closure', '1']
    self.do_run(src, 'success', force_c=True, js_engines=js_engines)

  @also_with_noderawfs
  def test_fs_nodefs_cloexec(self, js_engines=[NODE_JS]):
    src = open(path_from_root('tests', 'fs', 'test_nodefs_cloexec.c'), 'r').read()
    self.do_run(src, 'success', force_c=True, js_engines=js_engines)

  def test_fs_nodefs_home(self):
    self.set_setting('FORCE_FILESYSTEM', 1)
    src = open(path_from_root('tests', 'fs', 'test_nodefs_home.c'), 'r').read()
    self.do_run(src, 'success', js_engines=[NODE_JS])

  def test_fs_trackingdelegate(self):
    src = path_from_root('tests', 'fs', 'test_trackingdelegate.c')
    out = path_from_root('tests', 'fs', 'test_trackingdelegate.out')
    self.do_run_from_file(src, out)

  @also_with_noderawfs
  def test_fs_writeFile(self, js_engines=None):
    self.emcc_args += ['-s', 'DISABLE_EXCEPTION_CATCHING=1'] # see issue 2334
    src = path_from_root('tests', 'fs', 'test_writeFile.cc')
    out = path_from_root('tests', 'fs', 'test_writeFile.out')
    self.do_run_from_file(src, out, js_engines=js_engines)

  @also_with_noderawfs
  def test_fs_write(self, js_engines=None):
    self.emcc_args = ['-s', 'MEMFS_APPEND_TO_TYPED_ARRAYS=1']
    src = path_from_root('tests', 'fs', 'test_write.cpp')
    out = path_from_root('tests', 'fs', 'test_write.out')
    self.do_run_from_file(src, out, js_engines=js_engines)

  @also_with_noderawfs
  def test_fs_emptyPath(self, js_engines=None):
    src = path_from_root('tests', 'fs', 'test_emptyPath.c')
    out = path_from_root('tests', 'fs', 'test_emptyPath.out')
    self.do_run_from_file(src, out, js_engines=js_engines)

  @also_with_noderawfs
  def test_fs_append(self, js_engines=None):
    src = open(path_from_root('tests', 'fs', 'test_append.c'), 'r').read()
    self.do_run(src, 'success', force_c=True, js_engines=js_engines)

  def test_fs_mmap(self):
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    for fs in ['MEMFS']:
      src = path_from_root('tests', 'fs', 'test_mmap.c')
      out = path_from_root('tests', 'fs', 'test_mmap.out')
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run_from_file(src, out)

  @also_with_noderawfs
  def test_fs_errorstack(self, js_engines=[NODE_JS]):
    # Enables strict mode, which may catch some strict-mode-only errors
    # so that users can safely work with strict JavaScript if enabled.
    post = '''
def process(filename):
  src = open(filename, 'r').read()
  open(filename, 'w').write('"use strict";\\n' + src)
'''

    self.set_setting('FORCE_FILESYSTEM', 1)
    self.do_run(r'''
      #include <emscripten.h>
      #include <iostream>
      int main(void) {
        std::cout << "hello world\n"; // should work with strict mode
        EM_ASM(
          try {
            FS.readFile('/dummy.txt');
          } catch (err) {
            err.stack = err.stack; // should be writable
            throw err;
          }
        );
        return 0;
      }
    ''', 'at Object.readFile', js_engines=js_engines, js_transform=post) # engines has different error stack format

  @also_with_noderawfs
  def test_fs_llseek(self, js_engines=None):
    self.set_setting('FORCE_FILESYSTEM', 1)
    src = open(path_from_root('tests', 'fs', 'test_llseek.c'), 'r').read()
    self.do_run(src, 'success', force_c=True, js_engines=js_engines)

  def test_unistd_access(self):
    self.clear()
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    src = open(path_from_root('tests', 'unistd', 'access.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'access.out'), 'r').read()
    for fs in ['MEMFS', 'NODEFS']:
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run(src, expected, js_engines=[NODE_JS])
    # Node.js fs.chmod is nearly no-op on Windows
    if not WINDOWS:
      Building.COMPILER_TEST_OPTS = orig_compiler_opts
      self.emcc_args += ['-s', 'NODERAWFS=1']
      self.do_run(src, expected, js_engines=[NODE_JS])

  def test_unistd_curdir(self):
    src = open(path_from_root('tests', 'unistd', 'curdir.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'curdir.out'), 'r').read()
    self.do_run(src, expected)

  @also_with_noderawfs
  def test_unistd_close(self, js_engines=None):
    src = open(path_from_root('tests', 'unistd', 'close.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'close.out'), 'r').read()
    self.do_run(src, expected, js_engines=js_engines)

  def test_unistd_confstr(self):
    src = open(path_from_root('tests', 'unistd', 'confstr.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'confstr.out'), 'r').read()
    self.do_run(src, expected)

  def test_unistd_ttyname(self):
    src = open(path_from_root('tests', 'unistd', 'ttyname.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  @also_with_noderawfs
  def test_unistd_pipe(self, js_engines=None):
    src = open(path_from_root('tests', 'unistd', 'pipe.c'), 'r').read()
    self.do_run(src, 'success', force_c=True, js_engines=js_engines)

  @also_with_noderawfs
  def test_unistd_dup(self, js_engines=None):
    src = open(path_from_root('tests', 'unistd', 'dup.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'dup.out'), 'r').read()
    self.do_run(src, expected, js_engines=js_engines)

  def test_unistd_pathconf(self):
    src = open(path_from_root('tests', 'unistd', 'pathconf.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'pathconf.out'), 'r').read()
    self.do_run(src, expected)

  def test_unistd_truncate(self):
    self.clear()
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    for fs in ['MEMFS', 'NODEFS']:
      src = open(path_from_root('tests', 'unistd', 'truncate.c'), 'r').read()
      expected = open(path_from_root('tests', 'unistd', 'truncate.out'), 'r').read()
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run(src, expected, js_engines=[NODE_JS])

  @no_windows("Windows throws EPERM rather than EACCES or EINVAL")
  @unittest.skipIf(os.geteuid() == 0, "Root access invalidates this test by being able to write on readonly files")
  def test_unistd_truncate_noderawfs(self):
    self.emcc_args += ['-s', 'NODERAWFS=1']
    test_path = path_from_root('tests', 'unistd', 'truncate')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output, js_engines=[NODE_JS])

  def test_unistd_swab(self):
    src = open(path_from_root('tests', 'unistd', 'swab.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'swab.out'), 'r').read()
    self.do_run(src, expected)

  def test_unistd_isatty(self):
    src = open(path_from_root('tests', 'unistd', 'isatty.c'), 'r').read()
    self.do_run(src, 'success', force_c=True)

  def test_unistd_sysconf(self):
    src = open(path_from_root('tests', 'unistd', 'sysconf.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'sysconf.out'), 'r').read()
    self.do_run(src, expected)

  def test_unistd_sysconf_phys_pages(self):
    src = open(path_from_root('tests', 'unistd', 'sysconf_phys_pages.c'), 'r').read()
    if self.get_setting('ALLOW_MEMORY_GROWTH'):
      expected = (2 * 1024 * 1024 * 1024 - 16777216) // 16384
    else:
      expected = 16 * 1024 * 1024 // 16384
    self.do_run(src, str(expected) + ', errno: 0')

  def test_unistd_login(self):
    src = open(path_from_root('tests', 'unistd', 'login.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'login.out'), 'r').read()
    self.do_run(src, expected)

  def test_unistd_unlink(self):
    self.clear()
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    src = open(path_from_root('tests', 'unistd', 'unlink.c'), 'r').read()
    for fs in ['MEMFS', 'NODEFS']:
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      # symlinks on node.js on Windows require administrative privileges, so skip testing those bits on that combination.
      if WINDOWS and fs == 'NODEFS':
        Building.COMPILER_TEST_OPTS += ['-DNO_SYMLINK=1']
      self.do_run(src, 'success', force_c=True, js_engines=[NODE_JS])
    # Several differences/bugs on Windows including https://github.com/nodejs/node/issues/18014
    if not WINDOWS:
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-DNODERAWFS']
      # 0 if root user
      if os.geteuid() == 0:
        Building.COMPILER_TEST_OPTS += ['-DSKIP_ACCESS_TESTS']
      self.emcc_args += ['-s', 'NODERAWFS=1']
      self.do_run(src, 'success', force_c=True, js_engines=[NODE_JS])

  def test_unistd_links(self):
    self.clear()
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    src = open(path_from_root('tests', 'unistd', 'links.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'links.out'), 'r').read()
    for fs in ['MEMFS', 'NODEFS']:
      if WINDOWS and fs == 'NODEFS':
        print('Skipping NODEFS part of this test for test_unistd_links on Windows, since it would require administrative privileges.', file=sys.stderr)
        # Also, other detected discrepancies if you do end up running this test on NODEFS:
        # test expects /, but Windows gives \ as path slashes.
        # Calling readlink() on a non-link gives error 22 EINVAL on Unix, but simply error 0 OK on Windows.
        continue
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run(src, expected, js_engines=[NODE_JS])

  @no_windows('Skipping NODEFS test, since it would require administrative privileges.')
  def test_unistd_symlink_on_nodefs(self):
    # Also, other detected discrepancies if you do end up running this test on NODEFS:
    # test expects /, but Windows gives \ as path slashes.
    # Calling readlink() on a non-link gives error 22 EINVAL on Unix, but simply error 0 OK on Windows.
    self.clear()
    src = open(path_from_root('tests', 'unistd', 'symlink_on_nodefs.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'symlink_on_nodefs.out'), 'r').read()
    self.do_run(src, expected, js_engines=[NODE_JS])

  def test_unistd_sleep(self):
    src = open(path_from_root('tests', 'unistd', 'sleep.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'sleep.out'), 'r').read()
    self.do_run(src, expected)

  def test_unistd_io(self):
    self.clear()
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    src = open(path_from_root('tests', 'unistd', 'io.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'io.out'), 'r').read()
    for fs in ['MEMFS', 'NODEFS']:
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run(src, expected, js_engines=[NODE_JS])

  def test_unistd_misc(self):
    orig_compiler_opts = Building.COMPILER_TEST_OPTS[:]
    src = open(path_from_root('tests', 'unistd', 'misc.c'), 'r').read()
    expected = open(path_from_root('tests', 'unistd', 'misc.out'), 'r').read()
    for fs in ['MEMFS', 'NODEFS']:
      Building.COMPILER_TEST_OPTS = orig_compiler_opts + ['-D' + fs]
      self.do_run(src, expected, js_engines=[NODE_JS])

  def test_posixtime(self):
    test_path = path_from_root('tests', 'core', 'test_posixtime')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.banned_js_engines = [V8_ENGINE] # v8 lacks monotonic time
    self.do_run_from_file(src, output)

    if V8_ENGINE in JS_ENGINES:
      self.banned_js_engines = [engine for engine in JS_ENGINES if engine != V8_ENGINE]
      self.do_run_from_file(src, test_path + '_no_monotonic.out')
    else:
      print('(no v8, skipping no-monotonic case)')

  def test_uname(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_uname')

  def test_unary_literal(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_unary_literal')

  def test_env(self):
    src = open(path_from_root('tests', 'env', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'env', 'output.txt'), 'r').read()
    self.do_run(src, [
      expected.replace('{{{ THIS_PROGRAM }}}', os.path.join(self.get_dir(), 'src.cpp.o.js').replace('\\', '/')), # node, can find itself properly
      expected.replace('{{{ THIS_PROGRAM }}}', './this.program') # spidermonkey, v8
    ])

  def test_environ(self):
    src = open(path_from_root('tests', 'env', 'src-mini.c'), 'r').read()
    expected = open(path_from_root('tests', 'env', 'output-mini.txt'), 'r').read()
    self.do_run(src, [
      expected.replace('{{{ THIS_PROGRAM }}}', os.path.join(self.get_dir(), 'src.cpp.o.js').replace('\\', '/')), # node, can find itself properly
      expected.replace('{{{ THIS_PROGRAM }}}', './this.program') # spidermonkey, v8
    ])

  def test_systypes(self):
    src = open(path_from_root('tests', 'systypes', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'systypes', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_getloadavg(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_getloadavg')

  def test_nl_types(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_nl_types')

  def test_799(self):
    src = open(path_from_root('tests', '799.cpp'), 'r').read()
    self.do_run(src, '''Set PORT family: 0, port: 3979
Get PORT family: 0
PORT: 3979
''')

  def test_ctype(self):
    src = open(path_from_root('tests', 'ctype', 'src.c'), 'r').read()
    expected = open(path_from_root('tests', 'ctype', 'output.txt'), 'r').read()
    self.do_run(src, expected)

  def test_strcasecmp(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_strcasecmp')

  def test_atomic(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_atomic')

  @no_wasm_backend('wasm has 64bit lockfree atomics')
  def test_atomic_cxx(self):
    test_path = path_from_root('tests', 'core', 'test_atomic_cxx')
    src, output = (test_path + s for s in ('.cpp', '.txt'))
    Building.COMPILER_TEST_OPTS += ['-std=c++11']
    self.do_run_from_file(src, output)

    if self.get_setting('ALLOW_MEMORY_GROWTH') == 0 and not self.is_wasm():
      print('main module')
      self.set_setting('MAIN_MODULE', 1)
      self.do_run_from_file(src, output)

  def test_phiundef(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_phiundef')

  def test_netinet_in(self):
    src = open(path_from_root('tests', 'netinet', 'in.cpp'), 'r').read()
    expected = open(path_from_root('tests', 'netinet', 'in.out'), 'r').read()
    self.do_run(src, expected)

  @no_wasm_backend('No dynamic linking support in wasm backend path')
  def test_main_module_static_align(self):
    if self.get_setting('ALLOW_MEMORY_GROWTH'):
      self.skipTest('no shared modules with memory growth')
    self.set_setting('MAIN_MODULE', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_main_module_static_align')

  # libc++ tests

  def test_iostream_and_determinism(self):
    src = '''
      #include <iostream>

      int main()
      {
        std::cout << "hello world" << std::endl << 77 << "." << std::endl;
        return 0;
      }
    '''
    num = 5

    def test():
      print('(iteration)')
      time.sleep(random.random() / (10 * num)) # add some timing nondeterminism here, not that we need it, but whatever
      self.do_run(src, 'hello world\n77.\n')
      ret = open('src.cpp.o.js', 'rb').read()
      if self.get_setting('WASM'):
        ret += open('src.cpp.o.wasm', 'rb').read()
      return ret

    builds = [test() for i in range(num)]
    print(list(map(len, builds)))
    uniques = set(builds)
    if len(uniques) != 1:
      i = 0
      for unique in uniques:
        open('unique_' + str(i) + '.js', 'wb').write(unique)
        i += 1
      assert 0, 'builds must be deterministic, see unique_X.js'

  def test_stdvec(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_stdvec')

  def test_random_device(self):
    Building.COMPILER_TEST_OPTS += ['-std=c++11']

    self.do_run_in_out_file_test('tests', 'core', 'test_random_device')

  def test_reinterpreted_ptrs(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_reinterpreted_ptrs')

  def test_js_libraries(self):
    open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write('''
      #include <stdio.h>
      extern "C" {
        extern void printey();
        extern int calcey(int x, int y);
      }
      int main() {
        printey();
        printf("*%d*\\n", calcey(10, 22));
        return 0;
      }
    ''')
    open(os.path.join(self.get_dir(), 'mylib1.js'), 'w').write('''
      mergeInto(LibraryManager.library, {
        printey: function() {
          out('hello from lib!');
        }
      });
    ''')
    open(os.path.join(self.get_dir(), 'mylib2.js'), 'w').write('''
      mergeInto(LibraryManager.library, {
        calcey: function(x, y) {
          return x + y;
        }
      });
    ''')

    self.emcc_args += ['--js-library', os.path.join(self.get_dir(), 'mylib1.js'), '--js-library', os.path.join(self.get_dir(), 'mylib2.js')]
    self.do_run(open(os.path.join(self.get_dir(), 'main.cpp'), 'r').read(), 'hello from lib!\n*32*\n')

  def test_unicode_js_library(self):
    open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write('''
      #include <stdio.h>
      extern "C" {
        extern void printey();
      }
      int main() {
        printey();
        return 0;
      }
    ''')
    self.emcc_args += ['--js-library', path_from_root('tests', 'unicode_library.js')]
    self.do_run(open(os.path.join(self.get_dir(), 'main.cpp'), 'r').read(), u'Unicode snowman \u2603 says hello!')

  def test_js_lib_dep_memset(self):
    open('lib.js', 'w').write(r'''
mergeInto(LibraryManager.library, {
  depper__deps: ['memset'],
  depper: function(ptr) {
    _memset(ptr, 'd'.charCodeAt(0), 10);
  },
});
''')
    src = r'''
#include <string.h>
#include <stdio.h>

extern "C" {
extern void depper(char*);
}

int main(int argc, char** argv) {
  char buffer[11];
  buffer[10] = '\0';
  // call by a pointer, to force linking of memset, no llvm intrinsic here
  volatile auto ptr = memset;
  (*ptr)(buffer, 'a', 10);
  depper(buffer);
  puts(buffer);
}
'''
    self.emcc_args += ['--js-library', 'lib.js',  '-std=c++11']
    self.do_run(src, 'dddddddddd')
    # TODO(sbc): It seems that INCLUDE_FULL_LIBRARY will generally generate
    # undefined symbols at link time so perhaps have it imply this setting?
    self.set_setting('WARN_ON_UNDEFINED_SYMBOLS', 0)
    self.set_setting('INCLUDE_FULL_LIBRARY', 1)
    self.do_run(src, 'dddddddddd')

  def test_funcptr_import_type(self):
    self.emcc_args += ['--js-library', path_from_root('tests', 'core', 'test_funcptr_import_type.js'), '-std=c++11']
    self.do_run_in_out_file_test('tests', 'core', 'test_funcptr_import_type')

  def test_constglobalunion(self):
    self.emcc_args += ['-s', 'EXPORT_ALL=1']

    self.do_run(r'''
#include <stdio.h>

struct one_const {
  long a;
};

struct two_consts {
  long a;
  long b;
};

union some_consts {
  struct one_const one;
  struct two_consts two;
};

union some_consts my_consts = {{
  1
}};

struct one_const addr_of_my_consts = {
  (long)(&my_consts)
};

int main(void) {
  printf("%li\n", (long)!!addr_of_my_consts.a);
  return 0;
}
    ''', '1')

  ### 'Medium' tests

  def test_fannkuch(self):
    results = [(1, 0), (2, 1), (3, 2), (4, 4), (5, 7), (6, 10), (7, 16), (8, 22)]
    for i, j in results:
      src = open(path_from_root('tests', 'fannkuch.cpp'), 'r').read()
      self.do_run(src, 'Pfannkuchen(%d) = %d.' % (i, j), [str(i)], no_build=i > 1)

  def test_raytrace(self):
      # TODO: Should we remove this test?
      self.skipTest('Relies on double value rounding, extremely sensitive')

      src = open(path_from_root('tests', 'raytrace.cpp'), 'r').read().replace('double', 'float')
      output = open(path_from_root('tests', 'raytrace.ppm'), 'r').read()
      self.do_run(src, output, ['3', '16']) # , build_ll_hook=self.do_autodebug)

  def test_fasta(self):
      results = [(1, '''GG*ctt**tgagc*'''),
                 (20, '''GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTT*cttBtatcatatgctaKggNcataaaSatgtaaaDcDRtBggDtctttataattcBgtcg**tacgtgtagcctagtgtttgtgttgcgttatagtctatttgtggacacagtatggtcaaa**tgacgtcttttgatctgacggcgttaacaaagatactctg*'''),
                 (50, '''GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGA*TCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACAT*cttBtatcatatgctaKggNcataaaSatgtaaaDcDRtBggDtctttataattcBgtcg**tactDtDagcctatttSVHtHttKtgtHMaSattgWaHKHttttagacatWatgtRgaaa**NtactMcSMtYtcMgRtacttctWBacgaa**agatactctgggcaacacacatacttctctcatgttgtttcttcggacctttcataacct**ttcctggcacatggttagctgcacatcacaggattgtaagggtctagtggttcagtgagc**ggaatatcattcgtcggtggtgttaatctatctcggtgtagcttataaatgcatccgtaa**gaatattatgtttatttgtcggtacgttcatggtagtggtgtcgccgatttagacgtaaa**ggcatgtatg*''')]
      for precision in [0, 1, 2]:
        self.set_setting('PRECISE_F32', precision)
        for t in ['float', 'double']:
          print(precision, t)
          src = open(path_from_root('tests', 'fasta.cpp'), 'r').read().replace('double', t)
          for i, j in results:
            self.do_run(src, j, [str(i)], lambda x, err: x.replace('\n', '*'), no_build=i > 1)
          shutil.copyfile('src.cpp.o.js', '%d_%s.js' % (precision, t))

  def test_whets(self):
    self.do_run(open(path_from_root('tests', 'whets.cpp')).read(), 'Single Precision C Whetstone Benchmark')

  def test_dlmalloc(self):
    self.set_setting('MALLOC', "dlmalloc")

    self.banned_js_engines = [NODE_JS] # slower, and fail on 64-bit
    # needed with typed arrays
    self.set_setting('TOTAL_MEMORY', 128 * 1024 * 1024)

    src = open(path_from_root('system', 'lib', 'dlmalloc.c'), 'r').read() + '\n\n\n' + open(path_from_root('tests', 'dlmalloc_test.c'), 'r').read()
    self.do_run(src, '*1,0*', ['200', '1'])
    self.do_run(src, '*400,0*', ['400', '400'], no_build=True)

    # Linked version
    src = open(path_from_root('tests', 'dlmalloc_test.c'), 'r').read()
    self.do_run(src, '*1,0*', ['200', '1'])
    self.do_run(src, '*400,0*', ['400', '400'], no_build=True)

    # TODO: do this in other passes too, passing their opts into emcc
    if self.emcc_args == []:
      # emcc should build in dlmalloc automatically, and do all the sign correction etc. for it

      try_delete(os.path.join(self.get_dir(), 'src.cpp.o.js'))
      run_process([PYTHON, EMCC, path_from_root('tests', 'dlmalloc_test.c'), '-s', 'TOTAL_MEMORY=128MB', '-o', os.path.join(self.get_dir(), 'src.cpp.o.js')], stdout=PIPE, stderr=self.stderr_redirect)

      self.do_run('x', '*1,0*', ['200', '1'], no_build=True)
      self.do_run('x', '*400,0*', ['400', '400'], no_build=True)

      # The same for new and all its variants
      src = open(path_from_root('tests', 'new.cpp')).read()
      for new, delete in [
        ('malloc(100)', 'free'),
        ('new char[100]', 'delete[]'),
        ('new Structy', 'delete'),
        ('new int', 'delete'),
        ('new Structy[10]', 'delete[]'),
      ]:
        self.do_run(src.replace('{{{ NEW }}}', new).replace('{{{ DELETE }}}', delete), '*1,0*')

  def test_dlmalloc_partial(self):
    # present part of the symbols of dlmalloc, not all
    src = open(path_from_root('tests', 'new.cpp')).read().replace('{{{ NEW }}}', 'new int').replace('{{{ DELETE }}}', 'delete') + '''
#include <new>

void *
operator new(size_t size) throw(std::bad_alloc)
{
printf("new %d!\\n", size);
return malloc(size);
}
'''
    self.do_run(src, 'new 4!\n*1,0*')

  def test_dlmalloc_partial_2(self):
    if 'SAFE_HEAP' in str(self.emcc_args):
      self.skipTest('we do unsafe stuff here')
    # present part of the symbols of dlmalloc, not all. malloc is harder to link than new which is weak.
    self.do_run_in_out_file_test('tests', 'core', 'test_dlmalloc_partial_2')

  def test_libcxx(self):
    self.do_run(open(path_from_root('tests', 'hashtest.cpp')).read(),
                'june -> 30\nPrevious (in alphabetical order) is july\nNext (in alphabetical order) is march')

    self.do_run('''
      #include <set>
      #include <stdio.h>
      int main() {
        std::set<int> *fetchOriginatorNums = new std::set<int>();
        fetchOriginatorNums->insert(171);
        printf("hello world\\n");
        return 0;
      }
      ''', 'hello world')

  def test_typeid(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_typeid')

  def test_static_variable(self):
    # needs atexit
    self.set_setting('EXIT_RUNTIME', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_static_variable')

  def test_fakestat(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_fakestat')

  def test_mmap(self):
    self.set_setting('TOTAL_MEMORY', 128 * 1024 * 1024)
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)

    test_path = path_from_root('tests', 'core', 'test_mmap')
    src, output = (test_path + s for s in ('.c', '.out'))

    self.do_run_from_file(src, output)
    self.do_run_from_file(src, output, force_c=True)

  def test_mmap_file(self):
    for extra_args in [[], ['--no-heap-copy']]:
      self.emcc_args += ['--embed-file', 'data.dat'] + extra_args
      x = 'data from the file........'
      s = ''
      while len(s) < 9000:
        if len(s) + len(x) < 9000:
          s += x
          continue
        s += '.'
      assert len(s) == 9000
      open(self.in_dir('data.dat'), 'w').write(s)
      src = open(path_from_root('tests', 'mmap_file.c')).read()
      self.do_run(src, '*\n' + s[0:20] + '\n' + s[4096:4096 + 20] + '\n*\n')

  @no_wasm_backend('FixFunctionBitcasts pass invalidates otherwise-ok function pointer casts')
  def test_cubescript(self):
    assert 'asm3' in core_test_modes
    if self.run_name == 'asm3':
      self.emcc_args += ['--closure', '1'] # Use closure here for some additional coverage

    Building.COMPILER_TEST_OPTS = [x for x in Building.COMPILER_TEST_OPTS if x != '-g'] # remove -g, so we have one test without it by default

    def test():
      self.do_run(path_from_root('tests', 'cubescript'), '*\nTemp is 33\n9\n5\nhello, everyone\n*', main_file='command.cpp')

    test()

    assert 'asm1' in core_test_modes
    if self.run_name == 'asm1':
      print('verifing postsets')
      generated = open('src.cpp.o.js').read()
      generated = re.sub(r'\n+[ \n]*\n+', '\n', generated)
      main = generated[generated.find('function runPostSets'):]
      main = main[:main.find('\n}')]
      assert main.count('\n') <= 7, ('must not emit too many js_transform: %d' % main.count('\n')) + ' : ' + main

    # TODO: wrappers for wasm modules
    if not self.is_wasm():
      print('relocatable')
      assert self.get_setting('RELOCATABLE') == self.get_setting('EMULATED_FUNCTION_POINTERS') == 0
      self.set_setting('RELOCATABLE', 1)
      self.set_setting('EMULATED_FUNCTION_POINTERS', 1)
      test()
      self.set_setting('RELOCATABLE', 0)
      self.set_setting('EMULATED_FUNCTION_POINTERS', 0)

    if not self.is_wasm():
      print('split memory')
      self.set_setting('SPLIT_MEMORY', 8 * 1024 * 1024)
      test()
      self.set_setting('SPLIT_MEMORY', 0)

    if self.is_emterpreter():
      print('emterpreter/async/assertions') # extra coverage
      self.emcc_args += ['-s', 'EMTERPRETIFY_ASYNC=1', '-s', 'ASSERTIONS=1']
      test()
      print('emterpreter/async/assertions/whitelist')
      self.emcc_args += ['-s', 'EMTERPRETIFY_WHITELIST=["_frexpl"]'] # test double call assertions
      test()

  def test_relocatable_void_function(self):
    self.set_setting('RELOCATABLE', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_relocatable_void_function')

  @SIMD
  def test_sse1(self):
    if 'SAFE_HEAP=1' in self.emcc_args and SPIDERMONKEY_ENGINE in JS_ENGINES:
      self.banned_js_engines += [SPIDERMONKEY_ENGINE]
      print('Skipping test_sse1 with SAFE_HEAP=1 on SpiderMonkey, since it fails due to NaN canonicalization.')
    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)

    orig_args = self.emcc_args
    for mode in [[], ['-s', 'SIMD=1']]:
      self.emcc_args = orig_args + mode + ['-msse']
      self.maybe_closure()

      self.do_run(open(path_from_root('tests', 'test_sse1.cpp'), 'r').read(), 'Success!')

  # ignore nans in some simd tests due to an LLVM regression still being investigated,
  # https://github.com/kripken/emscripten/issues/4435
  # https://llvm.org/bugs/show_bug.cgi?id=28510
  @staticmethod
  def ignore_nans(out, err=''):
    return '\n'.join([x for x in (out + '\n' + err).split('\n') if 'NaN' not in x])

  # Tests the full SSE1 API.
  @SIMD
  def test_sse1_full(self):
    run_process([CLANG, path_from_root('tests', 'test_sse1_full.cpp'), '-o', 'test_sse1_full', '-D_CRT_SECURE_NO_WARNINGS=1'] + shared.get_clang_native_args(), env=shared.get_clang_native_env(), stdout=PIPE)
    native_result = run_process('./test_sse1_full', stdout=PIPE).stdout

    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'SIMD=1']]:
      self.emcc_args = orig_args + mode + ['-I' + path_from_root('tests'), '-msse']
      self.maybe_closure()

      self.do_run(open(path_from_root('tests', 'test_sse1_full.cpp'), 'r').read(), self.ignore_nans(native_result), output_nicerizer=self.ignore_nans)

  # Tests the full SSE2 API.
  @SIMD
  def test_sse2_full(self):
    if self.run_name == 'asm1' or self.run_name == 'asm2f':
      self.skipTest("some i64 thing we can't legalize")
    import platform
    is_64bits = platform.architecture()[0] == '64bit'
    if not is_64bits:
      self.skipTest('This test requires 64-bit system, since it tests SSE2 intrinsics only available in 64-bit mode!')

    args = []
    if '-O0' in self.emcc_args:
      args += ['-D_DEBUG=1']
    run_process([CLANG, path_from_root('tests', 'test_sse2_full.cpp'), '-o', 'test_sse2_full', '-D_CRT_SECURE_NO_WARNINGS=1'] + args + shared.get_clang_native_args(), env=shared.get_clang_native_env(), stdout=PIPE)
    native_result = run_process('./test_sse2_full', stdout=PIPE).stdout

    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'SIMD=1']]:
      self.emcc_args = orig_args + mode + ['-I' + path_from_root('tests'), '-msse2'] + args
      self.maybe_closure()

      self.do_run(open(path_from_root('tests', 'test_sse2_full.cpp'), 'r').read(), self.ignore_nans(native_result), output_nicerizer=self.ignore_nans)

  # Tests the full SSE3 API.
  @SIMD
  def test_sse3_full(self):
    args = []
    if '-O0' in self.emcc_args:
      args += ['-D_DEBUG=1']
    run_process([CLANG, path_from_root('tests', 'test_sse3_full.cpp'), '-o', 'test_sse3_full', '-D_CRT_SECURE_NO_WARNINGS=1', '-msse3'] + args + shared.get_clang_native_args(), env=shared.get_clang_native_env(), stdout=PIPE)
    native_result = run_process('./test_sse3_full', stdout=PIPE).stdout

    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'SIMD=1']]:
      self.emcc_args = orig_args + mode + ['-I' + path_from_root('tests'), '-msse3'] + args
      self.do_run(open(path_from_root('tests', 'test_sse3_full.cpp'), 'r').read(), native_result)

  @SIMD
  def test_ssse3_full(self):
    args = []
    if '-O0' in self.emcc_args:
      args += ['-D_DEBUG=1']
    run_process([CLANG, path_from_root('tests', 'test_ssse3_full.cpp'), '-o', 'test_ssse3_full', '-D_CRT_SECURE_NO_WARNINGS=1', '-mssse3'] + args + shared.get_clang_native_args(), env=shared.get_clang_native_env(), stdout=PIPE)
    native_result = run_process('./test_ssse3_full', stdout=PIPE).stdout

    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'SIMD=1']]:
      self.emcc_args = orig_args + mode + ['-I' + path_from_root('tests'), '-mssse3'] + args
      self.do_run(open(path_from_root('tests', 'test_ssse3_full.cpp'), 'r').read(), native_result)

  @SIMD
  def test_sse4_1_full(self):
    args = []
    if '-O0' in self.emcc_args:
      args += ['-D_DEBUG=1']
    run_process([CLANG, path_from_root('tests', 'test_sse4_1_full.cpp'), '-o', 'test_sse4_1_full', '-D_CRT_SECURE_NO_WARNINGS=1', '-msse4.1'] + args + shared.get_clang_native_args(), env=shared.get_clang_native_env(), stdout=PIPE)
    native_result = run_process('./test_sse4_1_full', stdout=PIPE).stdout

    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)
    orig_args = self.emcc_args
    for mode in [[], ['-s', 'SIMD=1']]:
      self.emcc_args = orig_args + mode + ['-I' + path_from_root('tests'), '-msse4.1'] + args
      self.do_run(open(path_from_root('tests', 'test_sse4_1_full.cpp'), 'r').read(), native_result)

  @SIMD
  def test_simd(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd')

  @SIMD
  def test_simd2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd2')

  @SIMD
  def test_simd3(self):
    # SIMD currently requires Math.fround
    self.set_setting('PRECISE_F32', 1)
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.emcc_args = self.emcc_args + ['-msse2']
    test_path = path_from_root('tests', 'core', 'test_simd3')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd4(self):
    # test_simd4 is to test phi node handling of SIMD path
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd4')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd5(self):
    # test_simd5 is to test shufflevector of SIMD path
    self.do_run_in_out_file_test('tests', 'core', 'test_simd5')

  @SIMD
  def test_simd6(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    # test_simd6 is to test x86 min and max intrinsics on NaN and -0.0
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd6')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd7(self):
    # test_simd7 is to test negative zero handling: https://github.com/kripken/emscripten/issues/2791
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd7')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd8(self):
    # test_simd8 is to test unaligned load and store
    test_path = path_from_root('tests', 'core', 'test_simd8')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.emcc_args = self.emcc_args + ['-msse']
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd9(self):
    # test_simd9 is to test a bug where _mm_set_ps(0.f) would generate an expression that did not validate as asm.js
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd9')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd10(self):
    # test_simd10 is to test that loading and storing arbitrary bit patterns works in SSE1.
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd10')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd11(self):
    # test_simd11 is to test that _mm_movemask_ps works correctly when handling input floats with 0xFFFFFFFF NaN bit patterns.
    test_path = path_from_root('tests', 'core', 'test_simd11')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.emcc_args = self.emcc_args + ['-msse2']
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd12(self):
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd12')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd13(self):
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd13')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd14(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.emcc_args = self.emcc_args + ['-msse', '-msse2']
    test_path = path_from_root('tests', 'core', 'test_simd14')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd15(self):
    if any(opt in self.emcc_args for opt in ('-O1', '-Os', '-Oz')):
      self.skipTest('legalizing -O1/s/z output is much harder, and not worth it - we work on -O0 and -O2+')
    self.emcc_args = self.emcc_args + ['-msse', '-msse2']
    test_path = path_from_root('tests', 'core', 'test_simd15')
    src, output = (test_path + s for s in ('.c', '.out'))
    self.do_run_from_file(src, output)

  @SIMD
  def test_simd16(self):
    self.emcc_args = self.emcc_args + ['-msse', '-msse2']
    self.do_run_in_out_file_test('tests', 'core', 'test_simd16')

  @SIMD
  def test_simd_set_epi64x(self):
    self.emcc_args = self.emcc_args + ['-msse2']
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_set_epi64x')

  @SIMD
  def test_simd_float64x2(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_float64x2')

  @SIMD
  def test_simd_float32x4(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_float32x4')

  @SIMD
  def test_simd_int32x4(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_int32x4')

  @SIMD
  def test_simd_int16x8(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_int16x8')

  @SIMD
  def test_simd_int8x16(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_int8x16')

  @SIMD
  def test_simd_dyncall(self):
    self.emcc_args = self.emcc_args + ['-msse']
    test_path = path_from_root('tests', 'core', 'test_simd_dyncall')
    src, output = (test_path + s for s in ('.cpp', '.txt'))
    self.do_run_from_file(src, output)

  # Tests that the vector SIToFP instruction generates an appropriate Int->Float type conversion operator and not a bitcasting/reinterpreting conversion
  @SIMD
  def test_simd_sitofp(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_sitofp')

  @SIMD
  def test_simd_shift_right(self):
    self.do_run_in_out_file_test('tests', 'core', 'test_simd_shift_right')

  def test_gcc_unmangler(self):
    Building.COMPILER_TEST_OPTS += ['-I' + path_from_root('third_party')]

    self.do_run(open(path_from_root('third_party', 'gcc_demangler.c')).read(), '*d_demangle(char const*, int, unsigned int*)*', args=['_ZL10d_demanglePKciPj'])

  def test_lua(self):
    if self.emcc_args:
      self.emcc_args = ['-g1'] + self.emcc_args

    total_memory = self.get_setting('TOTAL_MEMORY')

    if self.is_emterpreter():
      self.set_setting('PRECISE_F32', 1)

    for aggro in ([0, 1] if self.get_setting('ASM_JS') and '-O2' in self.emcc_args else [0]):
      self.set_setting('AGGRESSIVE_VARIABLE_ELIMINATION', aggro)
      self.set_setting('TOTAL_MEMORY', total_memory)
      print(aggro)
      self.do_run('',
                  'hello lua world!\n17\n1\n2\n3\n4\n7',
                  args=['-e', '''print("hello lua world!");print(17);for x = 1,4 do print(x) end;print(10-3)'''],
                  libraries=self.get_library('lua', [os.path.join('src', 'lua'), os.path.join('src', 'liblua.a')], make=['make', 'generic'], configure=None),
                  includes=[path_from_root('tests', 'lua')],
                  output_nicerizer=lambda string, err: (string + err).replace('\n\n', '\n').replace('\n\n', '\n'))

  def get_freetype(self):
    self.set_setting('DEAD_FUNCTIONS', self.get_setting('DEAD_FUNCTIONS') + ['_inflateEnd', '_inflate', '_inflateReset', '_inflateInit2_'])

    return self.get_library('freetype',
                            os.path.join('objs', '.libs', 'libfreetype.a'))

  @no_windows('./configure scripts dont to run on windows.')
  def test_freetype(self):
    assert 'asm2g' in core_test_modes
    if self.run_name == 'asm2g':
      # flip for some more coverage here
      self.set_setting('ALIASING_FUNCTION_POINTERS', 1 - self.get_setting('ALIASING_FUNCTION_POINTERS'))

    self.add_pre_run("FS.createDataFile('/', 'font.ttf', %s, true, false, false);" % str(
      list(bytearray(open(path_from_root('tests', 'freetype', 'LiberationSansBold.ttf'), 'rb').read()))
    ))

    # Not needed for js, but useful for debugging
    shutil.copyfile(path_from_root('tests', 'freetype', 'LiberationSansBold.ttf'), os.path.join(self.get_dir(), 'font.ttf'))

    # Main
    for outlining in [0, 5000]:
      self.set_setting('OUTLINING_LIMIT', outlining)
      print('outlining:', outlining, file=sys.stderr)
      self.do_run(open(path_from_root('tests', 'freetype', 'main.c'), 'r').read(),
                  open(path_from_root('tests', 'freetype', 'ref.txt'), 'r').read(),
                  ['font.ttf', 'test!', '150', '120', '25'],
                  libraries=self.get_freetype(),
                  includes=[path_from_root('tests', 'freetype', 'include')])
      self.set_setting('OUTLINING_LIMIT', 0)

    # github issue 324
    print('[issue 324]')
    self.do_run(open(path_from_root('tests', 'freetype', 'main_2.c'), 'r').read(),
                open(path_from_root('tests', 'freetype', 'ref_2.txt'), 'r').read(),
                ['font.ttf', 'w', '32', '32', '25'],
                libraries=self.get_freetype(),
                includes=[path_from_root('tests', 'freetype', 'include')])

    print('[issue 324 case 2]')
    self.do_run(open(path_from_root('tests', 'freetype', 'main_3.c'), 'r').read(),
                open(path_from_root('tests', 'freetype', 'ref_3.txt'), 'r').read(),
                ['font.ttf', 'W', '32', '32', '0'],
                libraries=self.get_freetype(),
                includes=[path_from_root('tests', 'freetype', 'include')])

    print('[issue 324 case 3]')
    self.do_run('',
                open(path_from_root('tests', 'freetype', 'ref_4.txt'), 'r').read(),
                ['font.ttf', 'ea', '40', '32', '0'],
                no_build=True)

  def test_sqlite(self):
    # gcc -O3 -I/home/alon/Dev/emscripten/tests/sqlite -ldl src.c
    self.banned_js_engines = [NODE_JS] # OOM in older node
    if '-O' not in str(self.emcc_args):
      self.banned_js_engines += [SPIDERMONKEY_ENGINE] # SM bug 1066759
    if self.is_split_memory():
      self.skipTest('SM bug 1205121')

    self.set_setting('DISABLE_EXCEPTION_CATCHING', 1)
    self.set_setting('EXPORTED_FUNCTIONS', self.get_setting('EXPORTED_FUNCTIONS') + ['_sqlite3_open', '_sqlite3_close', '_sqlite3_exec', '_sqlite3_free', '_callback'])
    if self.get_setting('ASM_JS') == 1 and '-g' in self.emcc_args:
      print("disabling inlining") # without registerize (which -g disables), we generate huge amounts of code
      self.set_setting('INLINING_LIMIT', 50)

    # self.set_setting('OUTLINING_LIMIT', 60000)

    self.do_run(r'''
                      #define SQLITE_DISABLE_LFS
                      #define LONGDOUBLE_TYPE double
                      #define SQLITE_INT64_TYPE long long int
                      #define SQLITE_THREADSAFE 0
                ''' + open(path_from_root('tests', 'sqlite', 'sqlite3.c'), 'r').read() + open(path_from_root('tests', 'sqlite', 'benchmark.c'), 'r').read(),
                open(path_from_root('tests', 'sqlite', 'benchmark.txt'), 'r').read(),
                includes=[path_from_root('tests', 'sqlite')],
                force_c=True)

  def test_zlib(self):
    self.maybe_closure()

    assert 'asm2g' in core_test_modes
    if self.run_name == 'asm2g':
      self.emcc_args += ['-g4'] # more source maps coverage

    use_cmake_configure = WINDOWS
    if use_cmake_configure:
      make_args = []
      configure = [PYTHON, path_from_root('emcmake'), 'cmake', '.', '-DBUILD_SHARED_LIBS=OFF']
    else:
      make_args = ['libz.a']
      configure = ['sh', './configure']

    self.do_run(open(path_from_root('tests', 'zlib', 'example.c'), 'r').read(),
                open(path_from_root('tests', 'zlib', 'ref.txt'), 'r').read(),
                libraries=self.get_library('zlib', os.path.join('libz.a'), make_args=make_args, configure=configure),
                includes=[path_from_root('tests', 'zlib'), os.path.join(self.get_dir(), 'building', 'zlib')],
                force_c=True)

  def test_the_bullet(self): # Called thus so it runs late in the alphabetical cycle... it is long
    self.set_setting('DEAD_FUNCTIONS', ['__ZSt9terminatev'])

    asserts = self.get_setting('ASSERTIONS')

    for use_cmake in [False, True]: # If false, use a configure script to configure Bullet build.
      print('cmake', use_cmake)
      # Windows cannot run configure sh scripts.
      if WINDOWS and not use_cmake:
        continue

      # extra testing for ASSERTIONS == 2
      self.set_setting('ASSERTIONS', 2 if use_cmake else asserts)

      def test():
        self.do_run(open(path_from_root('tests', 'bullet', 'Demos', 'HelloWorld', 'HelloWorld.cpp'), 'r').read(),
                    [open(path_from_root('tests', 'bullet', 'output.txt'), 'r').read(), # different roundings
                     open(path_from_root('tests', 'bullet', 'output2.txt'), 'r').read(),
                     open(path_from_root('tests', 'bullet', 'output3.txt'), 'r').read(),
                     open(path_from_root('tests', 'bullet', 'output4.txt'), 'r').read()],
                    libraries=get_bullet_library(self, use_cmake),
                    includes=[path_from_root('tests', 'bullet', 'src')])
      test()

      # TODO: test only worked in non-fastcomp (well, this section)
      continue
      assert 'asm2g' in core_test_modes
      if self.run_name == 'asm2g' and not use_cmake:
        # Test forced alignment
        print('testing FORCE_ALIGNED_MEMORY', file=sys.stderr)
        old = open('src.cpp.o.js').read()
        self.set_setting('FORCE_ALIGNED_MEMORY', 1)
        test()
        new = open('src.cpp.o.js').read()
        print(len(old), len(new), old.count('tempBigInt'), new.count('tempBigInt'))
        assert len(old) > len(new)
        assert old.count('tempBigInt') > new.count('tempBigInt')

  @no_windows('depends on freetype, which uses a ./configure which donsnt run on windows.')
  def test_poppler(self):
    # The fontconfig symbols are all missing from the poppler build
    # e.g. FcConfigSubstitute
    self.set_setting('ERROR_ON_UNDEFINED_SYMBOLS', 0)

    def test():
      Building.COMPILER_TEST_OPTS += [
        '-I' + path_from_root('tests', 'freetype', 'include'),
        '-I' + path_from_root('tests', 'poppler', 'include')
      ]

      with open(os.path.join(self.get_dir(), 'paper.pdf.js'), 'w') as f:
        f.write(str(list(bytearray(open(path_from_root('tests', 'poppler', 'paper.pdf'), 'rb').read()))))

      with open('pre.js', 'w') as f:
        f.write('''
      Module.preRun = function() {
        FS.createDataFile('/', 'paper.pdf', eval(Module.read('paper.pdf.js')), true, false, false);
      };
      Module.postRun = function() {
        var FileData = MEMFS.getFileDataAsRegularArray(FS.root.contents['filename-1.ppm']);
        out("Data: " + JSON.stringify(FileData.map(function(x) { return unSign(x, 8) })));
      };
''')
      self.emcc_args += ['--pre-js', 'pre.js']

      freetype = self.get_freetype()

      # Poppler has some pretty glaring warning.  Suppress them to keep the
      # test output readable.
      Building.COMPILER_TEST_OPTS += [
          '-Wno-sentinel',
          '-Wno-logical-not-parentheses',
          '-Wno-unused-private-field',
          '-Wno-tautological-compare',
          '-Wno-unknown-pragmas',
      ]
      poppler = self.get_library('poppler',
                                 [os.path.join('utils', 'pdftoppm.o'),
                                  os.path.join('utils', 'parseargs.o'),
                                  os.path.join('poppler', '.libs', 'libpoppler.a')],
                                 env_init={'FONTCONFIG_CFLAGS': ' ', 'FONTCONFIG_LIBS': ' '},
                                 configure_args=['--disable-libjpeg', '--disable-libpng', '--disable-poppler-qt', '--disable-poppler-qt4', '--disable-cms', '--disable-cairo-output', '--disable-abiword-output', '--enable-shared=no'])

      # Combine libraries

      combined = os.path.join(self.get_dir(), 'poppler-combined.bc')
      Building.link(poppler + freetype, combined)

      self.do_ll_run(combined,
                     str(list(bytearray(open(path_from_root('tests', 'poppler', 'ref.ppm'), 'rb').read()))).replace(' ', ''),
                     args='-scale-to 512 paper.pdf filename'.split(' '))

    test()

    if self.supports_js_dfe():
      print("Testing poppler with ELIMINATE_DUPLICATE_FUNCTIONS set to 1", file=sys.stderr)
      num_original_funcs = self.count_funcs('src.cpp.o.js')
      self.set_setting('ELIMINATE_DUPLICATE_FUNCTIONS', 1)
      test()
      # Make sure that DFE ends up eliminating more than 200 functions (if we can view source)
      assert (num_original_funcs - self.count_funcs('src.cpp.o.js')) > 200

  def test_openjpeg(self):
    # remove -g, so we have one test without it by default
    Building.COMPILER_TEST_OPTS = [x for x in Building.COMPILER_TEST_OPTS if x != '-g']

    original_j2k = path_from_root('tests', 'openjpeg', 'syntensity_lobby_s.j2k')
    image_bytes = list(bytearray(open(original_j2k, 'rb').read()))
    with open('pre.js', 'w') as f:
      f.write("""
      Module.preRun = function() { FS.createDataFile('/', 'image.j2k', %s, true, false, false); };
      Module.postRun = function() {
        out('Data: ' + JSON.stringify(MEMFS.getFileDataAsRegularArray(FS.analyzePath('image.raw').object)));
      };
      """ % shared.line_splitter(str(image_bytes)))

    shutil.copy(path_from_root('tests', 'openjpeg', 'opj_config.h'), self.get_dir())

    lib = self.get_library('openjpeg',
                           [os.path.sep.join('codec/CMakeFiles/j2k_to_image.dir/index.c.o'.split('/')),
                            os.path.sep.join('codec/CMakeFiles/j2k_to_image.dir/convert.c.o'.split('/')),
                            os.path.sep.join('codec/CMakeFiles/j2k_to_image.dir/__/common/color.c.o'.split('/')),
                            os.path.join('bin', 'libopenjpeg.so.1.4.0')],
                           configure=['cmake', '.'],
                           # configure_args=['--enable-tiff=no', '--enable-jp3d=no', '--enable-png=no'],
                           make_args=[]) # no -j 2, since parallel builds can fail

    # We use doubles in JS, so we get slightly different values than native code. So we
    # check our output by comparing the average pixel difference
    def image_compare(output, err):
      # Get the image generated by JS, from the JSON.stringify'd array
      m = re.search('\[[\d, -]*\]', output)
      self.assertIsNotNone(m, 'Failed to find proper image output in: ' + output)
      # Evaluate the output as a python array
      js_data = eval(m.group(0))

      js_data = [x if x >= 0 else 256 + x for x in js_data] # Our output may be signed, so unsign it

      # Get the correct output
      true_data = bytearray(open(path_from_root('tests', 'openjpeg', 'syntensity_lobby_s.raw'), 'rb').read())

      # Compare them
      assert(len(js_data) == len(true_data))
      num = len(js_data)
      diff_total = js_total = true_total = 0
      for i in range(num):
        js_total += js_data[i]
        true_total += true_data[i]
        diff_total += abs(js_data[i] - true_data[i])
      js_mean = js_total / float(num)
      true_mean = true_total / float(num)
      diff_mean = diff_total / float(num)

      image_mean = 83.265
      # print '[image stats:', js_mean, image_mean, true_mean, diff_mean, num, ']'
      assert abs(js_mean - image_mean) < 0.01, [js_mean, image_mean]
      assert abs(true_mean - image_mean) < 0.01, [true_mean, image_mean]
      assert diff_mean < 0.01, diff_mean

      return output

    self.emcc_args += ['--minify', '0'] # to compare the versions
    self.emcc_args += ['--pre-js', 'pre.js']

    def do_test():
      self.do_run(open(path_from_root('tests', 'openjpeg', 'codec', 'j2k_to_image.c'), 'r').read(),
                  'Successfully generated', # The real test for valid output is in image_compare
                  '-i image.j2k -o image.raw'.split(' '),
                  libraries=lib,
                  includes=[path_from_root('tests', 'openjpeg', 'libopenjpeg'),
                            path_from_root('tests', 'openjpeg', 'codec'),
                            path_from_root('tests', 'openjpeg', 'common'),
                            os.path.join(self.get_build_dir(), 'openjpeg')],
                  force_c=True,
                  assert_returncode=0,
                  output_nicerizer=image_compare) # , build_ll_hook=self.do_autodebug)

    do_test()

    # extra testing
    if self.get_setting('ALLOW_MEMORY_GROWTH') == 1:
      print('no memory growth', file=sys.stderr)
      self.set_setting('ALLOW_MEMORY_GROWTH', 0)
      do_test()

  @no_wasm_backend("uses bitcode compiled with asmjs, and we don't have unified triples")
  def test_python(self):
    self.set_setting('EMULATE_FUNCTION_POINTER_CASTS', 1)
    # The python build contains several undefined symbols
    self.set_setting('ERROR_ON_UNDEFINED_SYMBOLS', 0)

    bitcode = path_from_root('tests', 'python', 'python.bc')
    pyscript = dedent('''\
      print '***'
      print "hello python world!"
      print [x*2 for x in range(4)]
      t=2
      print 10-3-t
      print (lambda x: x*2)(11)
      print '%f' % 5.47
      print {1: 2}.keys()
      print '***'
      ''')
    pyoutput = '***\nhello python world!\n[0, 2, 4, 6]\n5\n22\n5.470000\n[1]\n***'

    for lto in [0, 1]:
      print('lto:', lto)
      if lto == 1:
        self.emcc_args += ['--llvm-lto', '1']
      self.do_ll_run(bitcode, pyoutput, args=['-S', '-c', pyscript])

  def test_lifetime(self):
    self.do_ll_run(path_from_root('tests', 'lifetime.ll'), 'hello, world!\n')
    if '-O1' in self.emcc_args or '-O2' in self.emcc_args:
      assert 'a18' not in open(os.path.join(self.get_dir(), 'src.cpp.o.js')).read(), 'lifetime stuff and their vars must be culled'

  # Test cases in separate files. Note that these files may contain invalid .ll!
  # They are only valid enough for us to read for test purposes, not for llvm-as
  # to process.
  @no_wasm_backend("uses bitcode compiled with asmjs, and we don't have unified triples")
  def test_cases(self):
    if Building.LLVM_OPTS:
      self.skipTest("Our code is not exactly 'normal' llvm assembly")

    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)

    # These tests don't end up linking with libc due to a behaviour in emcc
    # where the llvm-link step is skipped when the the input is a single
    # object file.  Since most of them `printf` (which comes from JS) but
    # depends on `strlen` (which comes from musl) these tests almost all
    # have an undefined `strlen`, which happens to not get called.
    # TODO(sbc): Remove the specical case from emcc what bypasses llvm-link
    # and then remove this line?
    self.set_setting('ERROR_ON_UNDEFINED_SYMBOLS', 0)
    self.set_setting('WARN_ON_UNDEFINED_SYMBOLS', 0)

    emcc_args = self.emcc_args

    # The following tests link to libc, and must be run with EMCC_LEAVE_INPUTS_RAW = 0
    need_no_leave_inputs_raw = [
      'muli33_ta2', 'philoop_ta2', 'uadd_overflow_64_ta2', 'i64toi8star',
      'legalizer_ta2', 'quotedlabel', 'alignedunaligned', 'sillybitcast',
      'invokeundef', 'loadbitcastgep', 'sillybitcast2', 'legalizer_b_ta2',
      'emptystruct', 'entry3', 'atomicrmw_i64', 'atomicrmw_b_i64',
      'invoke_byval', 'i24_ce_fastcomp',
    ]

    skip_tests = [
      # invalid ir
      'aliasbitcast', 'structparam', 'issue_39', 'phinonexist', 'oob_ta2', 'phiself', 'invokebitcast',
      # pnacl limitations in ExpandStructRegs
      'structphiparam', 'callwithstructural_ta2', 'callwithstructural64_ta2', 'structinparam',
      # pnacl limitations in ExpandGetElementPtr
      '2xi40',
      # current fastcomp limitations FIXME
      'quoted',
      # TODO XXX
      'atomicrmw_unaligned'
    ]
    skip_emterp = [
      'funcptr', # test writes to memory we store out bytecode! test is invalid
      # uses simd
      'i1282vecnback'
    ]
    skip_wasm = [
      'i1282vecnback', # uses simd
      # casts a function pointer from (i32, i32)* to (i64)*, which happens to work in asm.js but is a general function pointer undefined behavior
      'call_inttoptr_i64',
    ]

    names = glob.glob(path_from_root('tests', 'cases', '*.ll'))
    names.sort()
    for name in names:
      shortname = os.path.splitext(name)[0]
      # TODO: test only worked in non-fastcomp (well, these cases)
      basename = os.path.basename(shortname)
      if basename in skip_tests:
        continue
      if self.is_emterpreter() and basename in skip_emterp:
        continue
      if self.is_wasm() and basename in skip_wasm:
        continue

      if basename in need_no_leave_inputs_raw:
        leave_inputs = '0'
        self.set_setting('FILESYSTEM', 1)
      else:
        leave_inputs = '1'
        # no libc is linked in; with FILESYSTEM=0 we have a chance at printfing anyhow
        self.set_setting('FILESYSTEM', 0)

      if '_noasm' in shortname and self.get_setting('ASM_JS'):
        print('case "%s" not relevant for asm.js' % shortname)
        continue

      print("Testing case '%s'..." % basename)
      output_file = path_from_root('tests', 'cases', shortname + '.txt')
      if os.path.exists(output_file):
        output = open(output_file, 'r').read()
      else:
        output = 'hello, world!'

      if output.rstrip() != 'skip':
        self.emcc_args = emcc_args
        if os.path.exists(shortname + '.emcc'):
          self.emcc_args += json.loads(open(shortname + '.emcc').read())

        with env_modify({'EMCC_LEAVE_INPUTS_RAW': leave_inputs}):
          self.do_ll_run(path_from_root('tests', 'cases', name), output)

      # Optional source checking, a python script that gets a global generated with the source
      src_checker = path_from_root('tests', 'cases', shortname + '.py')
      if os.path.exists(src_checker):
        generated = open('src.cpp.o.js').read() # noqa
        exec(open(src_checker).read())

  def test_fuzz(self):
    Building.COMPILER_TEST_OPTS += ['-I' + path_from_root('tests', 'fuzz', 'include'), '-w']
    # some of these tests - 2.c', '9.c', '19.c', '21.c', '20.cpp' - div or rem i32 by 0, which traps in wasm
    self.set_setting('BINARYEN_TRAP_MODE', 'clamp')

    skip_lto_tests = [
      # LLVM LTO bug
      '19.c', '18.cpp',
      # puts exists before LTO, but is not used; LTO cleans it out, but then creates uses to it (printf=>puts) XXX https://llvm.org/bugs/show_bug.cgi?id=23814
      '23.cpp'
    ]

    def run_all(x):
      print(x)
      for name in glob.glob(path_from_root('tests', 'fuzz', '*.c')) + glob.glob(path_from_root('tests', 'fuzz', '*.cpp')):
        # if os.path.basename(name) != '4.c':
        #   continue
        if 'newfail' in name:
          continue
        if os.path.basename(name).startswith('temp_fuzzcode'):
          continue
        # pnacl legalization issue, see https://code.google.com/p/nativeclient/issues/detail?id=4027
        if x == 'lto' and self.run_name in ['default', 'asm2f'] and os.path.basename(name) in ['8.c']:
          continue
        if x == 'lto' and self.run_name == 'default' and os.path.basename(name) in skip_lto_tests:
          continue
        if x == 'lto' and os.path.basename(name) in ['21.c']:
          continue # LLVM LTO bug

        print(name)
        self.do_run(open(path_from_root('tests', 'fuzz', name)).read(),
                    open(path_from_root('tests', 'fuzz', name + '.txt')).read(), force_c=name.endswith('.c'))

    run_all('normal')

    self.emcc_args += ['--llvm-lto', '1']

    run_all('lto')

  # Autodebug the code
  def do_autodebug(self, filename):
    Building.llvm_dis(filename)
    output = run_process([PYTHON, AUTODEBUGGER, filename + '.o.ll', filename + '.o.ll.ll'], stdout=PIPE, stderr=self.stderr_redirect).stdout
    assert 'Success.' in output, output
    # rebuild .bc
    # TODO: use code in do_autodebug_post for this
    self.prep_ll_run(filename, filename + '.o.ll.ll', force_recompile=True)

  # Autodebug the code, after LLVM opts. Will only work once!
  def do_autodebug_post(self, filename):
    if not hasattr(self, 'post'):
      print('Asking for post re-call')
      self.post = True
      return True
    print('Autodebugging during post time')
    delattr(self, 'post')
    output = run_process([PYTHON, AUTODEBUGGER, filename + '.o.ll', filename + '.o.ll.ll'], stdout=PIPE, stderr=self.stderr_redirect).stdout
    assert 'Success.' in output, output
    shutil.copyfile(filename + '.o.ll.ll', filename + '.o.ll')
    Building.llvm_as(filename)
    Building.llvm_dis(filename)

  def test_autodebug(self):
    if self.get_setting('WASM_OBJECT_FILES'):
      self.skipTest('autodebugging only works with bitcode objects')
    if Building.LLVM_OPTS:
      self.skipTest('LLVM opts mess us up')
    Building.COMPILER_TEST_OPTS += ['--llvm-opts', '0']

    # Run a test that should work, generating some code
    test_path = path_from_root('tests', 'core', 'test_structs')
    src = test_path + '.c'
    output = test_path + '.out'
    self.do_run_from_file(src, output, build_ll_hook=lambda x: False) # add an ll hook, to force ll generation

    filename = os.path.join(self.get_dir(), 'src.cpp')
    self.do_autodebug(filename)

    # Compare to each other, and to expected output
    self.do_ll_run(path_from_root('tests', filename + '.o.ll.ll'), 'AD:-1,1')

    # Test using build_ll_hook
    src = '''
        #include <stdio.h>

        char cache[256], *next = cache;

        int main()
        {
          cache[10] = 25;
          next[20] = 51;
          int x = cache[10];
          double y = 11.52;
          printf("*%d,%d,%.2f*\\n", x, cache[20], y);
          return 0;
        }
      '''
    self.do_run(src, '''AD:-1,1''', build_ll_hook=self.do_autodebug)

  ### Integration tests

  @sync
  def test_ccall(self):
    self.emcc_args.append('-Wno-return-stack-address')
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['ccall', 'cwrap'])
    post = '''
def process(filename):
  src = open(filename, 'r').read() + \'\'\'
      out('*');
      var ret;
      ret = Module['ccall']('get_int', 'number'); out([typeof ret, ret].join(','));
      ret = ccall('get_float', 'number'); out([typeof ret, ret.toFixed(2)].join(','));
      ret = ccall('get_bool', 'boolean'); out([typeof ret, ret].join(','));
      ret = ccall('get_string', 'string'); out([typeof ret, ret].join(','));
      ret = ccall('print_int', null, ['number'], [12]); out(typeof ret);
      ret = ccall('print_float', null, ['number'], [14.56]); out(typeof ret);
      ret = ccall('print_bool', null, ['boolean'], [true]); out(typeof ret);
      ret = ccall('print_string', null, ['string'], ["cheez"]); out(typeof ret);
      ret = ccall('print_string', null, ['array'], [[97, 114, 114, 45, 97, 121, 0]]); out(typeof ret); // JS array
      ret = ccall('print_string', null, ['array'], [new Uint8Array([97, 114, 114, 45, 97, 121, 0])]); out(typeof ret); // typed array
      ret = ccall('multi', 'number', ['number', 'number', 'number', 'string'], [2, 1.4, 3, 'more']); out([typeof ret, ret].join(','));
      var p = ccall('malloc', 'pointer', ['number'], [4]);
      setValue(p, 650, 'i32');
      ret = ccall('pointer', 'pointer', ['pointer'], [p]); out([typeof ret, getValue(ret, 'i32')].join(','));
      out('*');
      // part 2: cwrap
      var noThirdParam = Module['cwrap']('get_int', 'number');
      out(noThirdParam());
      var multi = Module['cwrap']('multi', 'number', ['number', 'number', 'number', 'string']);
      out(multi(2, 1.4, 3, 'atr'));
      out(multi(8, 5.4, 4, 'bret'));
      out('*');
      // part 3: avoid stack explosion and check it's restored correctly
      for (var i = 0; i < TOTAL_STACK/60; i++) {
        ccall('multi', 'number', ['number', 'number', 'number', 'string'], [0, 0, 0, '123456789012345678901234567890123456789012345678901234567890']);
      }
      out('stack is ok.');
      ccall('call_ccall_again', null);
  \'\'\'
  open(filename, 'w').write(src)
'''

    self.set_setting('EXPORTED_FUNCTIONS', self.get_setting('EXPORTED_FUNCTIONS') + ['_get_int', '_get_float', '_get_bool', '_get_string', '_print_int', '_print_float', '_print_bool', '_print_string', '_multi', '_pointer', '_call_ccall_again', '_malloc'])
    self.do_run_in_out_file_test('tests', 'core', 'test_ccall', js_transform=post)

    if '-O2' in self.emcc_args or self.is_emterpreter():
      print('with closure')
      self.emcc_args += ['--closure', '1']
      self.do_run_in_out_file_test('tests', 'core', 'test_ccall', js_transform=post)

  def test_dyncall(self):
    self.do_run_in_out_file_test('tests', 'core', 'dyncall')
    # test dyncall (and other runtime methods in support.js) can be exported
    self.emcc_args += ['-DEXPORTED']
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['dynCall', 'addFunction', 'lengthBytesUTF8'])
    self.do_run_in_out_file_test('tests', 'core', 'dyncall')

  def test_dyncall_specific(self):
    emcc_args = self.emcc_args[:]
    for which, exported_runtime_methods in [
        ('DIRECT', []),
        ('EXPORTED', []),
        ('FROM_OUTSIDE', ['dynCall_viii'])
      ]:
      print(which)
      self.emcc_args = emcc_args + ['-D' + which]
      self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', exported_runtime_methods)
      self.do_run_in_out_file_test('tests', 'core', 'dyncall_specific')

  def test_getValue_setValue(self):
    # these used to be exported, but no longer are by default
    def test(output_prefix='', args=[]):
      old = self.emcc_args[:]
      self.emcc_args += args
      self.do_run(open(path_from_root('tests', 'core', 'getValue_setValue.cpp')).read(),
                  open(path_from_root('tests', 'core', 'getValue_setValue' + output_prefix + '.txt')).read())
      self.emcc_args = old
    # see that direct usage (not on module) works. we don't export, but the use
    # keeps it alive through JSDCE
    test(args=['-DDIRECT'])
    # see that with assertions, we get a nice error message
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', [])
    self.set_setting('ASSERTIONS', 1)
    test('_assert')
    self.set_setting('ASSERTIONS', 0)
    # see that when we export them, things work on the module
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['getValue', 'setValue'])
    test()

  def test_FS_exports(self):
    # these used to be exported, but no longer are by default
    for use_files in (0, 1):
      print(use_files)

      def test(output_prefix='', args=[]):
        if use_files:
          args += ['-DUSE_FILES']
        print(args)
        old = self.emcc_args[:]
        self.emcc_args += args
        self.do_run(open(path_from_root('tests', 'core', 'FS_exports.cpp')).read(),
                    (open(path_from_root('tests', 'core', 'FS_exports' + output_prefix + '.txt')).read(),
                     open(path_from_root('tests', 'core', 'FS_exports' + output_prefix + '_2.txt')).read()))
        self.emcc_args = old

      # see that direct usage (not on module) works. we don't export, but the use
      # keeps it alive through JSDCE
      test(args=['-DDIRECT', '-s', 'FORCE_FILESYSTEM=1'])
      # see that with assertions, we get a nice error message
      self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', [])
      self.set_setting('ASSERTIONS', 1)
      test('_assert')
      self.set_setting('ASSERTIONS', 0)
      # see that when we export them, things work on the module
      self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['FS_createDataFile'])
      test(args=['-s', 'FORCE_FILESYSTEM=1'])

  def test_legacy_exported_runtime_numbers(self):
    # these used to be exported, but no longer are by default

    def test(output_prefix='', args=[]):
      old = self.emcc_args[:]
      self.emcc_args += args
      self.do_run(open(path_from_root('tests', 'core', 'legacy_exported_runtime_numbers.cpp')).read(),
                  open(path_from_root('tests', 'core', 'legacy_exported_runtime_numbers' + output_prefix + '.txt')).read())
      self.emcc_args = old

    # see that direct usage (not on module) works. we don't export, but the use
    # keeps it alive through JSDCE
    test(args=['-DDIRECT'])
    # see that with assertions, we get a nice error message
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', [])
    self.set_setting('ASSERTIONS', 1)
    test('_assert')
    self.set_setting('ASSERTIONS', 0)
    # see that when we export them, things work on the module
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ['ALLOC_DYNAMIC'])
    test()

  @no_wasm_backend('DEAD_FUNCTIONS elimination is done by the JSOptimizer')
  def test_dead_functions(self):
    src = r'''
      #include <stdio.h>
      extern "C" {
      __attribute__((noinline)) int unused(int x) {
        volatile int y = x;
        return y;
      }
      }
      int main(int argc, char **argv) {
        printf("*%d*\n", argc > 1 ? unused(1) : 2);
        return 0;
      }
    '''

    def test(expected, args=[], no_build=False):
      self.do_run(src, expected, args=args, no_build=no_build)
      return open(self.in_dir('src.cpp.o.js')).read()

    # Sanity check that it works and the dead function is emitted
    js = test('*1*', ['x'])
    test('*2*', no_build=True)
    if self.run_name in ['default', 'asm1', 'asm2g']:
      assert 'function _unused($' in js

    # Kill off the dead function, and check a code path using it aborts
    self.set_setting('DEAD_FUNCTIONS', ['_unused'])
    test('*2*')
    test('abort(', args=['x'], no_build=True)

    # Kill off a library function, check code aborts
    self.set_setting('DEAD_FUNCTIONS', ['_printf'])
    test('abort(')
    test('abort(', args=['x'], no_build=True)

  def test_pgo(self):
    if self.get_setting('ASM_JS'):
      self.skipTest('PGO does not work in asm mode')

    def run_all(name, src):
      print(name)

      def test(expected, args=[], no_build=False):
        self.do_run(src, expected, args=args, no_build=no_build)
        return open(self.in_dir('src.cpp.o.js')).read()

      # Sanity check that it works and the dead function is emitted
      js = test('*9*')
      assert 'function _unused(' in js

      # Run with PGO, see that unused is true to its name
      self.set_setting('PGO', 1)
      test("*9*\n-s DEAD_FUNCTIONS='[\"_free\",\"_unused\"]'")
      self.set_setting('PGO', 0)

      # Kill off the dead function, still works and it is not emitted
      self.set_setting('DEAD_FUNCTIONS', ['_unused'])
      js = test('*9*')
      assert 'function _unused($' not in js # no compiled code
      assert 'function _unused(' in js # lib-generated stub
      self.set_setting('DEAD_FUNCTIONS', [])

      # Run the same code with argc that uses the dead function, see abort
      test(('dead function: unused'), args=['a', 'b'], no_build=True)

    # Normal stuff
    run_all('normal', r'''
      #include <stdio.h>
      extern "C" {
      int used(int x) {
        if (x == 0) return -1;
        return used(x/3) + used(x/17) + x%5;
      }
      int unused(int x) {
        if (x == 0) return -1;
        return unused(x/4) + unused(x/23) + x%7;
      }
      }
      int main(int argc, char **argv) {
        printf("*%d*\n", argc == 3 ? unused(argv[0][0] + 1024) : used(argc + 1555));
        return 0;
      }
    ''')

    # Call by function pointer
    run_all('function pointers', r'''
      #include <stdio.h>
      extern "C" {
      int used(int x) {
        if (x == 0) return -1;
        return used(x/3) + used(x/17) + x%5;
      }
      int unused(int x) {
        if (x == 0) return -1;
        return unused(x/4) + unused(x/23) + x%7;
      }
      }
      typedef int (*ii)(int);
      int main(int argc, char **argv) {
        ii pointers[256];
        for (int i = 0; i < 256; i++) {
          pointers[i] = (i == 3) ? unused : used;
        }
        printf("*%d*\n", pointers[argc](argc + 1555));
        return 0;
      }
    ''')

  # TODO: test only worked in non-fastcomp
  def test_asm_pgo(self):
    self.skipTest('non-fastcomp is deprecated and fails in 3.5')

    src = open(path_from_root('tests', 'hello_libcxx.cpp')).read()
    output = 'hello, world!'

    self.do_run(src, output)
    shutil.move(self.in_dir('src.cpp.o.js'), self.in_dir('normal.js'))

    self.set_setting('ASM_JS', 0)
    self.set_setting('PGO', 1)
    self.do_run(src, output)
    self.set_setting('ASM_JS', 1)
    self.set_setting('PGO', 0)

    shutil.move(self.in_dir('src.cpp.o.js'), self.in_dir('pgo.js'))
    pgo_output = run_js(self.in_dir('pgo.js')).split('\n')[1]
    open('pgo_data.rsp', 'w').write(pgo_output)

    # with response file

    self.emcc_args += ['@pgo_data.rsp']
    self.do_run(src, output)
    self.emcc_args.pop()
    shutil.move(self.in_dir('src.cpp.o.js'), self.in_dir('pgoed.js'))

    before = len(open('normal.js').read())
    after = len(open('pgoed.js').read())
    assert after < 0.90 * before, [before, after] # expect a size reduction

    # with response in settings element itself

    open('dead_funcs', 'w').write(pgo_output[pgo_output.find('['):-1])
    self.emcc_args += ['-s', 'DEAD_FUNCTIONS=@' + self.in_dir('dead_funcs')]
    self.do_run(src, output)
    self.emcc_args.pop()
    self.emcc_args.pop()
    shutil.move(self.in_dir('src.cpp.o.js'), self.in_dir('pgoed2.js'))
    assert open('pgoed.js').read() == open('pgoed2.js').read()

    # with relative response in settings element itself

    open('dead_funcs', 'w').write(pgo_output[pgo_output.find('['):-1])
    self.emcc_args += ['-s', 'DEAD_FUNCTIONS=@dead_funcs']
    self.do_run(src, output)
    self.emcc_args.pop()
    self.emcc_args.pop()
    shutil.move(self.in_dir('src.cpp.o.js'), self.in_dir('pgoed2.js'))
    assert open('pgoed.js').read() == open('pgoed2.js').read()

  def test_response_file(self):
    with open('rsp_file', 'w') as f:
      response_data = '-o %s/response_file.o.js %s' % (self.get_dir(), path_from_root('tests', 'hello_world.cpp'))
      f.write(response_data.replace('\\', '\\\\'))
    run_process([PYTHON, EMCC, "@rsp_file"] + self.emcc_args)
    self.do_run('', 'hello, world', basename='response_file', no_build=True)

  def test_linker_response_file(self):
    objfile = os.path.join(self.get_dir(), 'response_file.o')
    run_process([PYTHON, EMCC, '-c', path_from_root('tests', 'hello_world.cpp'), '-o', objfile] + self.emcc_args)
    # This should expand into -Wl,--export=foo which will then be ignored
    # by emscripten, except when using the wasm backend (lld) in which case it
    # should pass the original flag to the linker.
    with open('rsp_file', 'w') as f:
      response_data = objfile + ' --export=foo'
      f.write(response_data.replace('\\', '\\\\'))
    run_process([PYTHON, EMCC, "-Wl,@rsp_file", '-o', os.path.join(self.get_dir(), 'response_file.o.js')] + self.emcc_args)
    self.do_run('', 'hello, world', basename='response_file', no_build=True)

  def test_exported_response(self):
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <emscripten.h>

      extern "C" {
        int other_function() { return 5; }
      }

      int main() {
        int x = EM_ASM_INT({ return Module._other_function() });
        emscripten_run_script_string(""); // Add a reference to a symbol that exists in src/deps_info.json to uncover issue #2836 in the test suite.
        printf("waka %d!\n", x);
        return 0;
      }
    '''
    open('exps', 'w').write('["_main","_other_function"]')

    self.emcc_args += ['-s', 'EXPORTED_FUNCTIONS=@exps']
    self.do_run(src, '''waka 5!''')
    assert 'other_function' in open('src.cpp.o.js').read()

  def test_large_exported_response(self):
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      #include <emscripten.h>

      extern "C" {
      '''

    js_funcs = []
    num_exports = 5000
    count = 0
    while count < num_exports:
        src += 'int exported_func_from_response_file_%d () { return %d;}\n' % (count, count)
        js_funcs.append('_exported_func_from_response_file_%d' % count)
        count += 1

    src += r'''
      }

      int main() {
        int x = EM_ASM_INT({ return Module._exported_func_from_response_file_4999() });
        emscripten_run_script_string(""); // Add a reference to a symbol that exists in src/deps_info.json to uncover issue #2836 in the test suite.
        printf("waka %d!\n", x);
        return 0;
      }
    '''

    js_funcs.append('_main')
    exported_func_json_file = os.path.join(self.get_dir(), 'large_exported_response.json')
    open(exported_func_json_file, 'w').write(json.dumps(js_funcs))

    self.emcc_args += ['-s', 'EXPORTED_FUNCTIONS=@' + exported_func_json_file]
    self.do_run(src, '''waka 4999!''')
    assert '_exported_func_from_response_file_1' in open('src.cpp.o.js').read()

  @sync
  def test_add_function(self):
    self.set_setting('INVOKE_RUN', 0)
    self.set_setting('RESERVED_FUNCTION_POINTERS', 1)

    test_path = path_from_root('tests', 'interop')
    src, expected = (os.path.join(test_path, s) for s in ('test_add_function.cpp', 'test_add_function.out'))

    post_js = os.path.join(test_path, 'test_add_function_post.js')
    self.emcc_args += ['--post-js', post_js]
    self.do_run_from_file(src, expected)

    if self.get_setting('ASM_JS'):
      self.set_setting('RESERVED_FUNCTION_POINTERS', 0)
      self.do_run(open(src).read(), '''Finished up all reserved function pointers. Use a higher value for RESERVED_FUNCTION_POINTERS.''')
      generated = open('src.cpp.o.js').read()
      assert 'jsCall_' not in generated
      self.set_setting('RESERVED_FUNCTION_POINTERS', 1)

      # flip the test
      self.set_setting('ALIASING_FUNCTION_POINTERS', 1 - self.get_setting('ALIASING_FUNCTION_POINTERS'))
      self.do_run_from_file(src, expected)

    assert 'asm2' in core_test_modes
    if self.run_name == 'asm2':
      print('closure')
      self.emcc_args += ['--closure', '1']
      self.do_run_from_file(src, expected)

    # when emulating, we use a wasm Table, but we can't just assign a JS function to it
    # TODO: wrap the JS in wasm, see settings.js
    if not self.is_wasm():
      print('function pointer emulation')
      self.set_setting('RESERVED_FUNCTION_POINTERS', 0)
      # with emulation, we don't need to reserve
      self.set_setting('EMULATED_FUNCTION_POINTERS', 1)
      self.do_run_from_file(src, expected)

  def test_getFuncWrapper_sig_alias(self):
    src = r'''
    #include <stdio.h>
    #include <emscripten.h>

    void func1(int a) {
      printf("func1\n");
    }
    void func2(int a, int b) {
      printf("func2\n");
    }

    int main() {
      EM_ASM({
        getFuncWrapper($0, 'vi')(0);
        getFuncWrapper($1, 'vii')(0, 0);
      }, func1, func2);
      return 0;
    }
    '''
    self.do_run(src, 'func1\nfunc2\n')

  def test_emulate_function_pointer_casts(self):
    self.set_setting('EMULATE_FUNCTION_POINTER_CASTS', 1)

    self.do_run(open(path_from_root('tests', 'core', 'test_emulate_function_pointer_casts.cpp')).read(),
                ('|1.266,1|',                 # asm.js, double <-> int
                 '|1.266,1413754136|')) # wasm, reinterpret the bits

  def test_demangle_stacks(self):
    self.set_setting('DEMANGLE_SUPPORT', 1)
    self.set_setting('ASSERTIONS', 1)
    # when optimizing function names are not preserved by default.
    if '-O' in str(self.emcc_args):
      self.emcc_args += ['--profiling-funcs', '--llvm-opts', '0']
    # in the emterpreter, we interpret code execution and control flow,
    # so there is nothing on the browser-visible stack for meaningful
    # stack traces. enabling profiling makes the emterpreter call through
    # stubs with the full names.
    if self.is_emterpreter():
      self.emcc_args += ['--profiling-funcs']
    self.do_run_in_out_file_test('tests', 'core', 'test_demangle_stacks')
    if 'ASSERTIONS' not in str(self.emcc_args):
      print('without assertions, the stack is not printed, but a message suggesting assertions is')
      self.set_setting('ASSERTIONS', 0)
      self.do_run_in_out_file_test('tests', 'core', 'test_demangle_stacks_noassert')

  @no_emterpreter
  @no_wasm_backend('lld does not generate symbol maps')
  def test_demangle_stacks_symbol_map(self):
    self.set_setting('DEMANGLE_SUPPORT', 1)
    if '-O' in str(self.emcc_args) and '-O0' not in self.emcc_args and '-O1' not in self.emcc_args and '-g' not in self.emcc_args:
      self.emcc_args += ['--llvm-opts', '0']
    else:
      self.skipTest("without opts, we don't emit a symbol map")
    self.emcc_args += ['--emit-symbol-map']
    self.do_run(open(path_from_root('tests', 'core', 'test_demangle_stacks.cpp')).read(), 'abort')
    # make sure the shortened name is the right one
    symbols = open('src.cpp.o.js.symbols').read().split('\n')
    for line in symbols:
      if ':' not in line:
        continue
      short, full = line.split(':')
      if 'Aborter' in full:
        short_aborter = short
        full_aborter = full
    print('full:', full_aborter, 'short:', short_aborter)
    if SPIDERMONKEY_ENGINE and os.path.exists(SPIDERMONKEY_ENGINE[0]):
      output = run_js('src.cpp.o.js', engine=SPIDERMONKEY_ENGINE, stderr=PIPE, full_output=True, assert_returncode=None)
      # we may see the full one, if -g, or the short one if not
      if ' ' + short_aborter + ' ' not in output and ' ' + full_aborter + ' ' not in output:
        # stack traces may also be ' name ' or 'name@' etc
        if '\n' + short_aborter + ' ' not in output and '\n' + full_aborter + ' ' not in output and 'wasm-function[' + short_aborter + ']' not in output:
          if '\n' + short_aborter + '@' not in output and '\n' + full_aborter + '@' not in output:
            self.assertContained(' ' + short_aborter + ' ' + '\n' + ' ' + full_aborter + ' ', output)

  def test_tracing(self):
    Building.COMPILER_TEST_OPTS += ['--tracing']

    self.do_run_in_out_file_test('tests', 'core', 'test_tracing')

  @no_wasm_backend('EVAL_CTORS does not work with wasm backend')
  def test_eval_ctors(self):
    if '-O2' not in str(self.emcc_args) or '-O1' in str(self.emcc_args):
      self.skipTest('need js optimizations')

    orig_args = self.emcc_args[:] + ['-s', 'EVAL_CTORS=0']

    print('leave printf in ctor')
    self.emcc_args = orig_args + ['-s', 'EVAL_CTORS=1']
    self.do_run(r'''
      #include <stdio.h>
      struct C {
        C() { printf("constructing!\n"); } // don't remove this!
      };
      C c;
      int main() {}
    ''', "constructing!\n")

    def get_code_size():
      if self.is_wasm():
        # Use number of functions as a for code size
        return self.count_wasm_contents('src.cpp.o.wasm', 'funcs')
      else:
        return os.path.getsize('src.cpp.o.js')

    def get_mem_size():
      if self.is_wasm():
        # Use number of functions as a for code size
        return self.count_wasm_contents('src.cpp.o.wasm', 'memory-data')
      if self.uses_memory_init_file():
        return os.path.getsize('src.cpp.o.js.mem')

      # otherwise we ignore memory size
      return 0

    def do_test(test):
      self.emcc_args = orig_args + ['-s', 'EVAL_CTORS=1']
      test()
      ec_code_size = get_code_size()
      ec_mem_size = get_mem_size()
      self.emcc_args = orig_args[:]
      test()
      code_size = get_code_size()
      mem_size = get_mem_size()
      if mem_size:
        print('mem: ', mem_size, '=>', ec_mem_size)
        self.assertGreater(ec_mem_size, mem_size)
      print('code:', code_size, '=>', ec_code_size)
      self.assertLess(ec_code_size, code_size)

    print('remove ctor of just assigns to memory')

    def test1():
      self.do_run(r'''
        #include <stdio.h>
        struct C {
          int x;
          C() {
            volatile int y = 10;
            y++;
            x = y;
          }
        };
        C c;
        int main() {
          printf("x: %d\n", c.x);
        }
      ''', "x: 11\n")

    do_test(test1)

    print('libcxx - remove 2 ctors from iostream code')

    src = open(path_from_root('tests', 'hello_libcxx.cpp')).read()
    output = 'hello, world!'

    def test2():
      self.do_run(src, output)
    do_test(test2)

    print('assertions too')
    self.set_setting('ASSERTIONS', 1)
    self.do_run(src, output)
    self.set_setting('ASSERTIONS', 0)

    print('remove just some, leave others')

    def test3():
      self.do_run(r'''
#include <iostream>
#include <string>

class std_string {
public:
  std_string(): ptr(nullptr) { std::cout << "std_string()\n"; }
  std_string(const char* s): ptr(s) { std::cout << "std_string(const char* s) " << std::endl; }
  std_string(const std_string& s): ptr(s.ptr) { std::cout << "std_string(const std_string& s) " << std::endl; }
  const char* data() const { return ptr; }
private:
  const char* ptr;
};

const std_string txtTestString("212121\0");
const std::string s2text("someweirdtext");

int main() {
  std::cout << s2text << std::endl;
  std::cout << txtTestString.data() << std::endl;
  std::cout << txtTestString.data() << std::endl;
  return 0;
}
      ''', '''std_string(const char* s) 
someweirdtext
212121
212121
''') # noqa
    do_test(test3)

  def test_embind(self):
    Building.COMPILER_TEST_OPTS += ['--bind']

    src = r'''
      #include <stdio.h>
      #include <emscripten/val.h>

      using namespace emscripten;

      int main() {
        val Math = val::global("Math");

        // two ways to call Math.abs
        printf("abs(-10): %d\n", Math.call<int>("abs", -10));
        printf("abs(-11): %d\n", Math["abs"](-11).as<int>());

        return 0;
      }
    '''
    self.do_run(src, 'abs(-10): 10\nabs(-11): 11')

  def test_embind_2(self):
    Building.COMPILER_TEST_OPTS += ['--bind', '--post-js', 'post.js']
    open('post.js', 'w').write('''
      function printLerp() {
          out('lerp ' + Module.lerp(100, 200, 66) + '.');
      }
    ''')
    src = r'''
      #include <stdio.h>
      #include <emscripten.h>
      #include <emscripten/bind.h>
      using namespace emscripten;
      int lerp(int a, int b, int t) {
          return (100 - t) * a + t * b;
      }
      EMSCRIPTEN_BINDINGS(my_module) {
          function("lerp", &lerp);
      }
      int main(int argc, char **argv) {
          EM_ASM(printLerp());
          return 0;
      }
    '''
    self.do_run(src, 'lerp 166')

  def test_embind_3(self):
    Building.COMPILER_TEST_OPTS += ['--bind', '--post-js', 'post.js']
    open('post.js', 'w').write('''
      function ready() {
        try {
          Module.compute(new Uint8Array([1,2,3]));
        } catch(e) {
          out(e);
        }
      }
    ''')
    src = r'''
      #include <emscripten.h>
      #include <emscripten/bind.h>
      using namespace emscripten;
      int compute(int array[]) {
          return 0;
      }
      EMSCRIPTEN_BINDINGS(my_module) {
          function("compute", &compute, allow_raw_pointers());
      }
      int main(int argc, char **argv) {
          EM_ASM(ready());
          return 0;
      }
    '''
    self.do_run(src, 'UnboundTypeError: Cannot call compute due to unbound types: Pi')

  @no_wasm_backend('long doubles are f128s in wasm backend')
  def test_embind_4(self):
    Building.COMPILER_TEST_OPTS += ['--bind', '--post-js', 'post.js']
    open('post.js', 'w').write('''
      function printFirstElement() {
        out(Module.getBufferView()[0]);
      }
    ''')
    src = r'''
      #include <emscripten.h>
      #include <emscripten/bind.h>
      #include <emscripten/val.h>
      #include <stdio.h>
      using namespace emscripten;

      const size_t kBufferSize = 1024;
      long double buffer[kBufferSize];
      val getBufferView(void) {
          val v = val(typed_memory_view(kBufferSize, buffer));
          return v;
      }
      EMSCRIPTEN_BINDINGS(my_module) {
          function("getBufferView", &getBufferView);
      }

      int main(int argc, char **argv) {
        buffer[0] = 107;
        EM_ASM(printFirstElement());
        return 0;
      }
    '''
    self.do_run(src, '107')

  def test_embind_5(self):
    Building.COMPILER_TEST_OPTS += ['--bind']
    self.do_run_in_out_file_test('tests', 'core', 'test_embind_5')

  def test_embind_float_constants(self):
    self.emcc_args += ['--bind']
    self.do_run_from_file(path_from_root('tests', 'embind', 'test_float_constants.cpp'),
                          path_from_root('tests', 'embind', 'test_float_constants.out'))

  def test_embind_negative_constants(self):
    self.emcc_args += ['--bind']
    self.do_run_from_file(path_from_root('tests', 'embind', 'test_negative_constants.cpp'),
                          path_from_root('tests', 'embind', 'test_negative_constants.out'))

  def test_embind_unsigned(self):
    self.emcc_args += ['--bind', '--std=c++11']
    self.do_run_from_file(path_from_root('tests', 'embind', 'test_unsigned.cpp'), path_from_root('tests', 'embind', 'test_unsigned.out'))

  def test_embind_val(self):
    self.emcc_args += ['--bind', '--std=c++11']
    self.do_run_from_file(path_from_root('tests', 'embind', 'test_val.cpp'), path_from_root('tests', 'embind', 'test_val.out'))

  def test_embind_f_no_rtti(self):
    self.emcc_args += ['--bind', '-fno-rtti', '-DEMSCRIPTEN_HAS_UNBOUND_TYPE_NAMES=0']
    src = r'''
      #include<emscripten/val.h>
      #include<stdio.h>

      int main(int argc, char** argv){
        printf("418\n");
        return 0;
      }
    '''
    self.do_run(src, '418')

  @sync
  @no_wasm_backend()
  def test_webidl(self):
    assert 'asm2' in core_test_modes
    if self.run_name == 'asm2':
      self.emcc_args += ['--closure', '1', '-g1'] # extra testing
      # avoid closure minified names competing with our test code in the global name space
      self.set_setting('MODULARIZE', 1)

    def do_test_in_mode(mode, allow_memory_growth):
      print('testing mode', mode, ', memory growth =', allow_memory_growth)
      # Force IDL checks mode
      os.environ['IDL_CHECKS'] = mode

      run_process([PYTHON, path_from_root('tools', 'webidl_binder.py'),
                   path_from_root('tests', 'webidl', 'test.idl'),
                   'glue'])
      assert os.path.exists('glue.cpp')
      assert os.path.exists('glue.js')

      # Export things on "TheModule". This matches the typical use pattern of the bound library
      # being used as Box2D.* or Ammo.*, and we cannot rely on "Module" being always present (closure may remove it).
      open('export.js', 'w').write('''
// test purposes: remove printErr output, whose order is unpredictable when compared to print
err = err = function(){};
''')
      self.emcc_args += ['-s', 'EXPORTED_FUNCTIONS=["_malloc"]', '--post-js', 'glue.js', '--post-js', 'export.js']
      if allow_memory_growth:
        self.emcc_args += ['-s', 'ALLOW_MEMORY_GROWTH=1']
      shutil.copyfile(path_from_root('tests', 'webidl', 'test.h'), self.in_dir('test.h'))
      shutil.copyfile(path_from_root('tests', 'webidl', 'test.cpp'), self.in_dir('test.cpp'))
      src = open('test.cpp').read()

      def post(filename):
        src = open(filename, 'a')
        src.write('\n\n')
        if self.run_name == 'asm2':
          src.write('var TheModule = Module();\n')
        else:
          src.write('var TheModule = Module;\n')
        src.write('\n\n')
        if allow_memory_growth:
          src.write("var isMemoryGrowthAllowed = true;")
        else:
          src.write("var isMemoryGrowthAllowed = false;")
        src.write(open(path_from_root('tests', 'webidl', 'post.js')).read())
        src.write('\n\n')
        src.close()

      output = open(path_from_root('tests', 'webidl', "output_%s.txt" % mode)).read()
      self.do_run(src, output, post_build=post, output_nicerizer=(lambda out, err: out))

    do_test_in_mode('ALL', False)
    do_test_in_mode('FAST', False)
    do_test_in_mode('DEFAULT', False)
    do_test_in_mode('ALL', True)

  ### Tests for tools

  def test_safe_heap(self):
    if not self.get_setting('SAFE_HEAP'):
      self.skipTest('We need SAFE_HEAP to test SAFE_HEAP')
    # TODO: Should we remove this test?
    self.skipTest('It is ok to violate the load-store assumption with TA2')
    if Building.LLVM_OPTS:
      self.skipTest('LLVM can optimize away the intermediate |x|')

    src = '''
      #include <stdio.h>
      #include <stdlib.h>
      int main() { int *x = (int*)malloc(sizeof(int));
        *x = 20;
        float *y = (float*)x;
        printf("%f\\n", *y);
        printf("*ok*\\n");
        return 0;
      }
    '''

    try:
      self.do_run(src, '*nothingatall*', assert_returncode=None)
    except Exception as e:
      # This test *should* fail, by throwing this exception
      assert 'Assertion failed: Load-store consistency assumption failure!' in str(e), str(e)

    self.set_setting('SAFE_HEAP', 1)

    # Linking multiple files should work too

    module = '''
      #include <stdio.h>
      #include <stdlib.h>
      void callFunc() { int *x = (int*)malloc(sizeof(int));
        *x = 20;
        float *y = (float*)x;
        printf("%f\\n", *y);
      }
    '''
    module_name = os.path.join(self.get_dir(), 'module.cpp')
    open(module_name, 'w').write(module)

    main = '''
      #include <stdio.h>
      #include <stdlib.h>
      extern void callFunc();
      int main() { callFunc();
        int *x = (int*)malloc(sizeof(int));
        *x = 20;
        float *y = (float*)x;
        printf("%f\\n", *y);
        printf("*ok*\\n");
        return 0;
      }
    '''
    main_name = os.path.join(self.get_dir(), 'main.cpp')
    open(main_name, 'w').write(main)

    Building.emcc(module_name, ['-g'])
    Building.emcc(main_name, ['-g'])
    all_name = os.path.join(self.get_dir(), 'all.bc')
    Building.link([module_name + '.o', main_name + '.o'], all_name)

    try:
      self.do_ll_run(all_name, '*nothingatall*', assert_returncode=None)
    except Exception as e:
      # This test *should* fail, by throwing this exception
      assert 'Assertion failed: Load-store consistency assumption failure!' in str(e), str(e)

  @no_emterpreter
  def test_source_map(self):
    if not jsrun.check_engine(NODE_JS):
      self.skipTest('sourcemapper requires Node to run')
    if '-g' not in Building.COMPILER_TEST_OPTS:
      Building.COMPILER_TEST_OPTS.append('-g')

    src = '''
      #include <stdio.h>
      #include <assert.h>

      __attribute__((noinline)) int foo() {
        printf("hi"); // line 6
        return 1; // line 7
      }

      int main() {
        printf("%d", foo()); // line 11
        return 0; // line 12
      }
    '''

    dirname = self.get_dir()
    src_filename = os.path.join(dirname, 'src.cpp')
    out_filename = os.path.join(dirname, 'a.out.js')
    wasm_filename = os.path.join(dirname, 'a.out.wasm')
    no_maps_filename = os.path.join(dirname, 'no-maps.out.js')

    with open(src_filename, 'w') as f:
      f.write(src)
    assert '-g4' not in Building.COMPILER_TEST_OPTS
    Building.emcc(src_filename,
                  self.serialize_settings() + self.emcc_args + Building.COMPILER_TEST_OPTS,
                  out_filename)
    # the file name may find its way into the generated code, so make sure we
    # can do an apples-to-apples comparison by compiling with the same file name
    shutil.move(out_filename, no_maps_filename)
    with open(no_maps_filename) as f:
      no_maps_file = f.read()
    no_maps_file = re.sub(' *//[@#].*$', '', no_maps_file, flags=re.MULTILINE)
    Building.COMPILER_TEST_OPTS.append('-g4')

    def build_and_check():
      Building.emcc(src_filename,
                    self.serialize_settings() + self.emcc_args + Building.COMPILER_TEST_OPTS,
                    out_filename,
                    stderr=PIPE)
      map_referent = out_filename if not self.get_setting('WASM') else wasm_filename
      # after removing the @line and @sourceMappingURL comments, the build
      # result should be identical to the non-source-mapped debug version.
      # this is worth checking because the parser AST swaps strings for token
      # objects when generating source maps, so we want to make sure the
      # optimizer can deal with both types.
      map_filename = map_referent + '.map'

      def encode_utf8(data):
        if isinstance(data, dict):
          for key in data:
            data[key] = encode_utf8(data[key])
          return data
        elif isinstance(data, list):
          for i in range(len(data)):
            data[i] = encode_utf8(data[i])
          return data
        elif isinstance(data, unicode):
          return data.encode('utf8')
        else:
          return data

      data = json.load(open(map_filename, 'r'))
      if str is bytes:
        # Python 2 compatibility
        data = encode_utf8(data)
      if hasattr(data, 'file'):
        # the file attribute is optional, but if it is present it needs to refer
        # the output file.
        self.assertPathsIdentical(map_referent, data['file'])
      assert len(data['sources']) == 1, data['sources']
      self.assertPathsIdentical(src_filename, data['sources'][0])
      if hasattr(data, 'sourcesContent'):
        # the sourcesContent attribute is optional, but if it is present it
        # needs to containt valid source text.
        self.assertTextDataIdentical(src, data['sourcesContent'][0])
      mappings = json.loads(jsrun.run_js(
        path_from_root('tools', 'source-maps', 'sourcemap2json.js'),
        shared.NODE_JS, [map_filename]))
      if str is bytes:
        # Python 2 compatibility
        mappings = encode_utf8(mappings)
      seen_lines = set()
      for m in mappings:
        self.assertPathsIdentical(src_filename, m['source'])
        seen_lines.add(m['originalLine'])
      # ensure that all the 'meaningful' lines in the original code get mapped
      assert seen_lines.issuperset([6, 7, 11, 12])

    build_and_check()

  def test_modularize_closure_pre(self):
    # test that the combination of modularize + closure + pre-js works. in that mode,
    # closure should not minify the Module object in a way that the pre-js cannot use it.
    base_args = self.emcc_args + [
      '--pre-js', path_from_root('tests', 'core', 'modularize_closure_pre.js'),
      '--closure', '1',
      '-g1'
    ]

    for instance in (0, 1):
      print("instance: %d" % instance)
      if instance:
        self.emcc_args = base_args + ['-s', 'MODULARIZE_INSTANCE=1']
      else:
        self.emcc_args = base_args + ['-s', 'MODULARIZE=1']

      def post(filename):
        with open(filename, 'a') as f:
          f.write('\n\n')
          if not instance:
            f.write('var TheModule = Module();\n')

      self.do_run_in_out_file_test('tests', 'core', 'modularize_closure_pre', post_build=post)

  @no_emterpreter
  @no_wasm('wasmifying destroys debug info and stack tracability')
  def test_exception_source_map(self):
    self.emcc_args.append('-g4')
    if not jsrun.check_engine(NODE_JS):
      self.skipTest('sourcemapper requires Node to run')

    src = '''
      #include <stdio.h>

      __attribute__((noinline)) void foo(int i) {
          if (i < 10) throw i; // line 5
      }

      #include <iostream>
      #include <string>

      int main() {
        std::string x = "ok"; // add libc++ stuff to make this big, test for #2410
        int i;
        scanf("%d", &i);
        foo(i);
        std::cout << x << std::endl;
        return 0;
      }
    '''

    def post(filename):
      map_filename = filename + '.map'
      assert os.path.exists(map_filename)
      mappings = json.loads(jsrun.run_js(
        path_from_root('tools', 'source-maps', 'sourcemap2json.js'),
        shared.NODE_JS, [map_filename]))
      with open(filename) as f:
        lines = f.readlines()
      for m in mappings:
        # -1 to fix 0-start vs 1-start
        if m['originalLine'] == 5 and '__cxa_throw' in lines[m['generatedLine'] - 1]:
          return
      assert False, 'Must label throw statements with line numbers'

    dirname = self.get_dir()
    self.build(src, dirname, os.path.join(dirname, 'src.cpp'), post_build=post)

  @no_wasm('wasmifying destroys debug info and stack tracability')
  def test_emscripten_log(self):
    self.banned_js_engines = [V8_ENGINE] # v8 doesn't support console.log
    self.emcc_args += ['-s', 'DEMANGLE_SUPPORT=1']
    if self.is_emterpreter():
      # without this, stack traces are not useful (we jump emterpret=>emterpret)
      self.emcc_args += ['--profiling-funcs']
      # even so, we get extra emterpret() calls on the stack
      Building.COMPILER_TEST_OPTS += ['-DEMTERPRETER']
    if self.get_setting('ASM_JS'):
      # XXX Does not work in SpiderMonkey since callstacks cannot be captured when running in asm.js, see https://bugzilla.mozilla.org/show_bug.cgi?id=947996
      self.banned_js_engines += [SPIDERMONKEY_ENGINE]
    if '-g' not in Building.COMPILER_TEST_OPTS:
      Building.COMPILER_TEST_OPTS.append('-g')
    Building.COMPILER_TEST_OPTS += ['-DRUN_FROM_JS_SHELL']
    self.do_run(open(path_from_root('tests', 'emscripten_log', 'emscripten_log.cpp')).read(), '''test print 123

12.345679 9.123457 1.353180

12345678 9123456 1353179

12.345679 9123456 1353179

12345678 9.123457 1353179

12345678 9123456 1.353180

12345678 9.123457 1.353180

12.345679 9123456 1.353180

12.345679 9.123457 1353179

Success!
''')
    # test closure compiler as well
    if self.run_name == 'asm2':
      print('closure')
      self.emcc_args += ['--closure', '1', '-g1'] # extra testing
      self.do_run_in_out_file_test('tests', 'emscripten_log', 'emscripten_log_with_closure')

  def test_float_literals(self):
    self.do_run_in_out_file_test('tests', 'test_float_literals')

  def test_exit_status(self):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    src = r'''
      #include <stdio.h>
      #include <stdlib.h>
      static void cleanup() {
        printf("cleanup\n");
      }

      int main() {
        atexit(cleanup); // this atexit should still be called
        printf("hello, world!\n");
        // Unusual exit status to make sure it's working!
        if (CAPITAL_EXIT) {
          _Exit(118);
        } else {
          exit(118);
        }
      }
    '''
    with open('pre.js', 'w') as f:
      f.write('''
      Module.preInit = function() {
        addOnExit(function () {
          out('I see exit status: ' + EXITSTATUS);
        });
      }
      ''')
    self.emcc_args += ['--pre-js', 'pre.js']
    self.do_run(src.replace('CAPITAL_EXIT', '0'), 'hello, world!\ncleanup\nI see exit status: 118')
    self.do_run(src.replace('CAPITAL_EXIT', '1'), 'hello, world!\ncleanup\nI see exit status: 118')

  def test_noexitruntime(self):
    src = r'''
      #include <emscripten.h>
      #include <stdio.h>
      static int testPre = TEST_PRE;
      struct Global {
        Global() {
          printf("in Global()\n");
          if (testPre) { EM_ASM(Module['noExitRuntime'] = true;); }
        }
        ~Global() { printf("ERROR: in ~Global()\n"); }
      } global;
      int main() {
        if (!testPre) { EM_ASM(Module['noExitRuntime'] = true;); }
        printf("in main()\n");
      }
    '''
    self.do_run(src.replace('TEST_PRE', '0'), 'in Global()\nin main()')
    self.do_run(src.replace('TEST_PRE', '1'), 'in Global()\nin main()')

  def test_minmax(self):
    self.do_run(open(path_from_root('tests', 'test_minmax.c')).read(), 'NAN != NAN\nSuccess!')

  def test_locale(self):
    self.do_run_from_file(path_from_root('tests', 'test_locale.c'), path_from_root('tests', 'test_locale.out'))

  def test_vswprintf_utf8(self):
    self.do_run_from_file(path_from_root('tests', 'vswprintf_utf8.c'), path_from_root('tests', 'vswprintf_utf8.out'))

  def test_async(self, emterpretify=False):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    self.banned_js_engines = [SPIDERMONKEY_ENGINE, V8_ENGINE] # needs setTimeout which only node has

    if not emterpretify:
      if self.is_emterpreter():
        self.skipTest("don't test both emterpretify and asyncify at once")
      self.set_setting('ASYNCIFY', 1)
    else:
      self.set_setting('EMTERPRETIFY', 1)
      self.set_setting('EMTERPRETIFY_ASYNC', 1)

    src = r'''
#include <stdio.h>
#include <emscripten.h>
void f(void *p) {
  *(int*)p = 99;
  printf("!");
}
int main() {
  int i = 0;
  printf("Hello");
  emscripten_async_call(f, &i, 1);
  printf("World");
  emscripten_%s(100);
  printf("%%d\n", i);
}
''' % ('sleep_with_yield' if emterpretify else 'sleep')

    self.do_run(src, 'HelloWorld!99')

    if emterpretify:
      print('check bad ccall use')
      src = r'''
#include <stdio.h>
#include <emscripten.h>
int main() {
  printf("Hello");
  emscripten_sleep(100);
  printf("World\n");
}
'''
      self.set_setting('ASSERTIONS', 1)
      self.set_setting('INVOKE_RUN', 0)
      open('pre.js', 'w').write('''
Module['onRuntimeInitialized'] = function() {
  try {
    ccall('main', 'number', ['number', 'string'], [2, 'waka']);
    var never = true;
  } catch(e) {
    out(e);
    assert(!never);
  }
};
''')
      self.emcc_args += ['--pre-js', 'pre.js']
      self.do_run(src, 'The call to main is running asynchronously.')

      print('check reasonable ccall use')
      src = r'''
#include <stdio.h>
#include <emscripten.h>
int main() {
  printf("Hello");
  emscripten_sleep(100);
  printf("World\n");
}
'''
      open('pre.js', 'w').write('''
Module['onRuntimeInitialized'] = function() {
  ccall('main', null, ['number', 'string'], [2, 'waka'], { async: true });
};
''')
      self.do_run(src, 'HelloWorld')

      print('check ccall promise')
      self.set_setting('EXPORTED_FUNCTIONS', ['_stringf', '_floatf'])
      src = r'''
#include <stdio.h>
#include <emscripten.h>
extern "C" {
  char* stringf(char* param) {
    emscripten_sleep(20);
    printf(param);
    return "second";
  }
  double floatf() {
    emscripten_sleep(20);
    emscripten_sleep(20);
    return 6.4;
  }
}
'''
      open('pre.js', 'w').write(r'''
Module['onRuntimeInitialized'] = function() {
  ccall('stringf', 'string', ['string'], ['first\n'], { async: true })
    .then(function(val) {
      console.log(val);
      ccall('floatf', 'number', null, null, { async: true }).then(console.log);
    });
};
''')
      self.do_run(src, 'first\nsecond\n6.4')

  @no_wasm_backend('EMTERPRETIFY causes JSOptimizer to run, which is '
                   'unsupported with Wasm backend')
  def test_async_emterpretify(self):
    self.test_async(emterpretify=True)

  def test_async_returnvalue(self):
    if not self.is_emterpreter():
      self.skipTest('emterpreter-only test')

    self.set_setting('EMTERPRETIFY_ASYNC', 1)
    self.banned_js_engines = [SPIDERMONKEY_ENGINE, V8_ENGINE] # needs setTimeout which only node has

    open('lib.js', 'w').write(r'''
mergeInto(LibraryManager.library, {
  sleep_with_return__deps: ['$EmterpreterAsync'],
  sleep_with_return: function(ms) {
    return EmterpreterAsync.handle(function(resume) {
      var startTime = Date.now();
      setTimeout(function() {
        if (ABORT) return; // do this manually; we can't call into Browser.safeSetTimeout, because that is paused/resumed!
        resume(function() {
          return Date.now() - startTime;
        });
      }, ms);
    });
  }
});
''')

    src = r'''
#include <stdio.h>
#include <assert.h>
#include <emscripten.h>

extern "C" {
extern int sleep_with_return(int ms);
}

int main() {
  int ms = sleep_with_return(1000);
  assert(ms >= 900);
  printf("napped for %d ms\n", ms);
}
'''
    self.emcc_args += ['--js-library', 'lib.js']
    self.do_run(src, 'napped')

  def test_async_exit(self):
    if not self.is_emterpreter():
      self.skipTest('emterpreter-only test')

    self.set_setting('EMTERPRETIFY_ASYNC', 1)
    self.banned_js_engines = [SPIDERMONKEY_ENGINE, V8_ENGINE] # needs setTimeout which only node has

    self.do_run(r'''
#include <stdio.h>
#include <stdlib.h>
#include <emscripten.h>

void f()
{
    printf("f\n");
    emscripten_sleep(1);
    printf("hello\n");
    static int i = 0;
    i++;
    if(i == 5) {
        printf("exit\n");
        exit(0);
        printf("world\n");
        i = 0;
    }
}

int main() {
    while(1) {
        f();
    }
    return 0;
}
''', 'f\nhello\nf\nhello\nf\nhello\nf\nhello\nf\nhello\nexit\n')

  def test_async_abort(self):
    if not self.is_emterpreter():
      self.skipTest('emterpreter-only test')

    self.banned_js_engines = [SPIDERMONKEY_ENGINE, V8_ENGINE] # needs setTimeout which only node has

    self.set_setting('EMTERPRETIFY_ASYNC', 1)

    open('lib.js', 'w').write(r'''
mergeInto(LibraryManager.library, {
  sleep_with_abort__deps: ['$EmterpreterAsync'],
  sleep_with_abort: function() {
    EmterpreterAsync.handle(function(resume) {
      setTimeout(function() {
        abort();
        setTimeout(function() {
          resume();
        }, 10);
      }, 10);
    });
  }
});
''')

    src = r'''
#include <stdio.h>

extern "C" {
extern void sleep_with_abort(void);
}

int main() {
    printf("Hello\n");
    sleep_with_abort();
    printf("ERROR\n");
    return 0;
}
'''

    self.emcc_args += ['--js-library', 'lib.js']
    self.do_run(src, 'Hello')

  def test_async_invoke_safe_heap(self):
    if not self.is_emterpreter():
      self.skipTest('emterpreter-only test')

    self.banned_js_engines = [SPIDERMONKEY_ENGINE, V8_ENGINE] # needs setTimeout which only node has

    # SAFE_HEAP leads to SAFE_FT_MASK, which appear in dynCall_*
    # and then if they are interpreted, that messes up reloading
    # of the stack (we can't run emterpreted code at that time,
    # we should just see calls and follow them).
    self.set_setting('EMTERPRETIFY_ASYNC', 1)
    self.set_setting('SAFE_HEAP', 1)
    self.set_setting('EXPORTED_FUNCTIONS', ['_async_callback_test'])
    self.set_setting('EXTRA_EXPORTED_RUNTIME_METHODS', ["ccall"])
    self.set_setting('DISABLE_EXCEPTION_CATCHING', 0)
    self.set_setting('ALLOW_MEMORY_GROWTH', 1)
    self.set_setting('EMTERPRETIFY', 1)
    self.set_setting('EMTERPRETIFY_ASYNC', 1)
    self.set_setting('ASSERTIONS', 2)

    open('post.js', 'w').write(r'''
var AsyncOperation = {
  done: false,

  start: function() {
    // this.done = true; // uncomment this line => no crash
    Promise.resolve().then(function() {
      console.log('done!');
      AsyncOperation.done = true;
    });
  }
};

Module.ccall('async_callback_test', null, [], [], { async: true });
''')

    src = r'''
#include <stdio.h>
#include <emscripten.h>

extern "C" {
  void call_async_operation() {
    printf("start\n");
    EM_ASM({AsyncOperation.start()});
    printf("mid\n");
    while (!EM_ASM_INT({return AsyncOperation.done})) {
      printf("sleep1\n");
      emscripten_sleep(200);
      printf("sleep2\n");
    }
  }

  // remove throw() => no crash
  static void nothrow_func() throw()
  {
    call_async_operation();
    printf("async operation OK\n");
  }

  void async_callback_test() {
    nothrow_func();
  }
}'''

    self.emcc_args += [
      '--post-js', 'post.js',
      '--profiling-funcs',
      '--minify', '0',
      '--memory-init-file', '0'
    ]
    self.do_run(src, 'async operation OK')

  def do_test_coroutine(self, additional_settings):
    # needs to flush stdio streams
    self.set_setting('EXIT_RUNTIME', 1)
    src = open(path_from_root('tests', 'test_coroutines.cpp')).read()
    for (k, v) in additional_settings.items():
      self.set_setting(k, v)
    self.do_run(src, '*leaf-0-100-1-101-1-102-2-103-3-104-5-105-8-106-13-107-21-108-34-109-*')

  def test_coroutine_asyncify(self):
    self.do_test_coroutine({'ASYNCIFY': 1})

  @no_wasm_backend('ASYNCIFY is not supported in the LLVM wasm backend')
  def test_asyncify_unused(self):
    # test a program not using asyncify, but the pref is set
    self.set_setting('ASYNCIFY', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')

  @no_wasm_backend('EMTERPRETIFY causes JSOptimizer to run, which is '
                   'unsupported with Wasm backend')
  def test_coroutine_emterpretify_async(self):
    # The same EMTERPRETIFY_WHITELIST should be in other.test_emterpreter_advise
    self.do_test_coroutine({'EMTERPRETIFY': 1, 'EMTERPRETIFY_ASYNC': 1, 'EMTERPRETIFY_WHITELIST': ['_fib', '_f', '_g'], 'ASSERTIONS': 1})

  @no_emterpreter
  @no_wasm_backend('EMTERPRETIFY causes JSOptimizer to run, which is '
                   'unsupported with Wasm backend')
  def test_emterpretify(self):
    self.set_setting('EMTERPRETIFY', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')
    print('async')
    self.set_setting('EMTERPRETIFY_ASYNC', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')

  def test_cxx_self_assign(self):
    # See https://github.com/kripken/emscripten/pull/2688 and http://llvm.org/bugs/show_bug.cgi?id=18735
    open('src.cpp', 'w').write(r'''
      #include <map>
      #include <stdio.h>

      int main() {
        std::map<int, int> m;
        m[0] = 1;
        m = m;
        // size should still be one after self assignment
        if (m.size() == 1) {
          printf("ok.\n");
        }
      }
      ''')
    run_process([PYTHON, EMCC, 'src.cpp'] + self.emcc_args)
    self.assertContained('ok.', run_js('a.out.js', args=['C']))

  def test_memprof_requirements(self):
    # This test checks for the global variables required to run the memory
    # profiler.  It would fail if these variables were made no longer global
    # or if their identifiers were changed.
    open(os.path.join(self.get_dir(), 'main.cpp'), 'w').write('''
      extern "C" {
        void check_memprof_requirements();
      }
      int main() {
        check_memprof_requirements();
        return 0;
      }
    ''')
    open(os.path.join(self.get_dir(), 'lib.js'), 'w').write('''
      mergeInto(LibraryManager.library, {
        check_memprof_requirements: function() {
          if (typeof TOTAL_MEMORY === 'number' &&
              typeof STATIC_BASE === 'number' &&
              typeof STATICTOP === 'number' &&
              typeof STACK_BASE === 'number' &&
              typeof STACK_MAX === 'number' &&
              typeof STACKTOP === 'number' &&
              typeof DYNAMIC_BASE === 'number' &&
              typeof DYNAMICTOP_PTR === 'number') {
             out('able to run memprof');
           } else {
             out('missing the required variables to run memprof');
           }
        }
      });
    ''')
    self.emcc_args += ['--js-library', os.path.join(self.get_dir(), 'lib.js')]
    self.do_run(open(os.path.join(self.get_dir(), 'main.cpp'), 'r').read(), 'able to run memprof')

  def test_fs_dict(self):
    self.set_setting('FORCE_FILESYSTEM', 1)
    open(self.in_dir('pre.js'), 'w').write('''
      Module = {};
      Module['preRun'] = function() {
          out(typeof FS.filesystems['MEMFS']);
          out(typeof FS.filesystems['IDBFS']);
          out(typeof FS.filesystems['NODEFS']);
      };
    ''')
    self.emcc_args += ['--pre-js', 'pre.js']
    self.do_run('int main() { return 0; }', 'object\nobject\nobject')

  @sync
  @no_wasm_backend("wasm backend has no support for fastcomp's -emscripten-assertions flag")
  def test_stack_overflow_check(self):
    args = self.emcc_args + ['-s', 'TOTAL_STACK=1048576']
    self.emcc_args = args + ['-s', 'STACK_OVERFLOW_CHECK=1', '-s', 'ASSERTIONS=0']
    self.do_run(open(path_from_root('tests', 'stack_overflow.cpp'), 'r').read(), 'Stack overflow! Stack cookie has been overwritten' if not self.get_setting('SAFE_HEAP') else 'segmentation fault')

    self.emcc_args = args + ['-s', 'STACK_OVERFLOW_CHECK=2', '-s', 'ASSERTIONS=0']
    self.do_run(open(path_from_root('tests', 'stack_overflow.cpp'), 'r').read(), 'Stack overflow! Attempted to allocate')

    self.emcc_args = args + ['-s', 'ASSERTIONS=1']
    self.do_run(open(path_from_root('tests', 'stack_overflow.cpp'), 'r').read(), 'Stack overflow! Attempted to allocate')

  @no_wasm_backend('Wasm backend emits non-trapping float-to-int conversion')
  def test_binaryen_trap_mode(self):
    if not self.is_wasm():
      self.skipTest('wasm test')
    TRAP_OUTPUTS = ('trap', 'RuntimeError')
    default = self.get_setting('BINARYEN_TRAP_MODE')
    print('default is', default)
    for mode in ['js', 'clamp', 'allow', '']:
      if mode == 'js' and self.is_wasm_backend():
        # wasm backend does not use asm2wasm imports, which js trap mode requires
        continue
      print('mode:', mode)
      self.set_setting('BINARYEN_TRAP_MODE', mode or default)
      if not mode:
        mode = default
      print('  idiv')
      self.do_run(open(path_from_root('tests', 'wasm', 'trap-idiv.cpp')).read(), {
          'js': '|0|',
          'clamp': '|0|',
          'allow': TRAP_OUTPUTS
        }[mode])
      print('  f2i')
      self.do_run(open(path_from_root('tests', 'wasm', 'trap-f2i.cpp')).read(), {
          'js': '|1337|\n|4294967295|', # JS did an fmod 2^32 | normal
          'clamp': '|-2147483648|\n|4294967295|',
          'allow': TRAP_OUTPUTS
        }[mode])

  def test_sbrk(self):
    self.do_run(open(path_from_root('tests', 'sbrk_brk.cpp')).read(), 'OK.')

  def test_brk(self):
    self.emcc_args += ['-DTEST_BRK=1']
    self.do_run(open(path_from_root('tests', 'sbrk_brk.cpp')).read(), 'OK.')

  # Tests that we can use the dlmalloc mallinfo() function to obtain information about malloc()ed blocks and compute how much memory is used/freed.
  def test_mallinfo(self):
    self.do_run(open(path_from_root('tests', 'mallinfo.cpp')).read(), 'OK.')

  def test_wrap_malloc(self):
    self.do_run(open(path_from_root('tests', 'wrap_malloc.cpp')).read(), 'OK.')

  def test_environment(self):
    self.set_setting('ASSERTIONS', 1)
    for engine in JS_ENGINES:
      for work in (1, 0):
        # set us to test in just this engine
        self.banned_js_engines = [e for e in JS_ENGINES if e != engine]
        # tell the compiler to build with just that engine
        if engine == NODE_JS and work:
          self.set_setting('ENVIRONMENT', 'node')
        else:
          self.set_setting('ENVIRONMENT', 'shell')
        print(engine, work, self.get_setting('ENVIRONMENT'))
        try:
          self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')
        except Exception as e:
          if not work:
            self.assertContained('not compiled for this environment', str(e))
          else:
            raise
        js = open('src.cpp.o.js').read()
        assert ('require(' in js) == (self.get_setting('ENVIRONMENT') == 'node'), 'we should have require() calls only if node js specified'

  def test_dfe(self):
    if not self.supports_js_dfe():
      self.skipTest('dfe-only')
    self.set_setting('ELIMINATE_DUPLICATE_FUNCTIONS', 1)
    self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')
    self.emcc_args += ['-g2'] # test for issue #6331
    self.do_run_in_out_file_test('tests', 'core', 'test_hello_world')

  def test_postrun_exception(self):
    # verify that an exception thrown in postRun() will not trigger the
    # compilation failed handler, and will be printed to stderr.
    self.add_post_run('ThisFunctionDoesNotExist()')
    src = open(path_from_root('tests', 'core', 'test_hello_world.c')).read()
    self.build(src, self.get_dir(), 'src.c')
    output = run_js('src.c.o.js', assert_returncode=None, stderr=STDOUT)
    self.assertNotContained('failed to asynchronously prepare wasm', output)
    self.assertContained('hello, world!', output)
    self.assertContained('ThisFunctionDoesNotExist is not defined', output)


# Generate tests for everything
def make_run(name, emcc_args=None, env=None):
  if env is None:
    env = {}

  TT = type(name, (TestCoreBase,), dict(run_name=name, env=env))  # noqa

  def tearDown(self):
    try:
      super(TT, self).tearDown()
    finally:
      for k, v in self.env.items():
        del os.environ[k]

      # clear global changes to Building
      Building.COMPILER_TEST_OPTS = []
      Building.LLVM_OPTS = 0

  TT.tearDown = tearDown

  def setUp(self):
    super(TT, self).setUp()
    for k, v in self.env.items():
      assert k not in os.environ, k + ' should not be in environment'
      os.environ[k] = v

    os.chdir(self.get_dir()) # Ensure the directory exists and go there

    assert emcc_args is not None
    self.emcc_args = emcc_args[:]
    Settings.load(self.emcc_args)
    Building.LLVM_OPTS = 0

    Building.COMPILER_TEST_OPTS += [
        '-Werror', '-Wno-dynamic-class-memaccess', '-Wno-format',
        '-Wno-format-extra-args', '-Wno-format-security',
        '-Wno-pointer-bool-conversion', '-Wno-unused-volatile-lvalue',
        '-Wno-c++11-compat-deprecated-writable-strings',
        '-Wno-invalid-pp-token', '-Wno-shift-negative-value'
    ]

    for arg in self.emcc_args:
      if arg.startswith('-O'):
        Building.COMPILER_TEST_OPTS.append(arg) # so bitcode is optimized too, this is for cpp to ll

  TT.setUp = setUp

  return TT


# Main asm.js test modes
asm0 = make_run('asm0', emcc_args=['-s', 'ASM_JS=2', '-s', 'WASM=0'])
asm1 = make_run('asm1', emcc_args=['-O1', '-s', 'WASM=0'])
asm2 = make_run('asm2', emcc_args=['-O2', '-s', 'WASM=0'])
asm3 = make_run('asm3', emcc_args=['-O3', '-s', 'WASM=0'])
asm2g = make_run('asm2g', emcc_args=['-O2', '-s', 'WASM=0', '-g', '-s', 'ASSERTIONS=1', '-s', 'SAFE_HEAP=1'])

# Main wasm test modes
binaryen0 = make_run('binaryen0', emcc_args=['-O0'])
binaryen1 = make_run('binaryen1', emcc_args=['-O1'])
binaryen2 = make_run('binaryen2', emcc_args=['-O2'])
binaryen3 = make_run('binaryen3', emcc_args=['-O3'])
binaryens = make_run('binaryens', emcc_args=['-Os'])
binaryenz = make_run('binaryenz', emcc_args=['-Oz'])

wasmobj0 = make_run('wasmobj0', emcc_args=['-O0', '-s', 'WASM_OBJECT_FILES=1'])
wasmobj1 = make_run('wasmobj1', emcc_args=['-O1', '-s', 'WASM_OBJECT_FILES=1'])
wasmobj2 = make_run('wasmobj2', emcc_args=['-O2', '-s', 'WASM_OBJECT_FILES=1'])
wasmobj3 = make_run('wasmobj3', emcc_args=['-O3', '-s', 'WASM_OBJECT_FILES=1'])
wasmobjs = make_run('wasmobjs', emcc_args=['-Os', '-s', 'WASM_OBJECT_FILES=1'])
wasmobjz = make_run('wasmobjz', emcc_args=['-Oz', '-s', 'WASM_OBJECT_FILES=1'])


# Secondary test modes - run directly when there is a specific need

# asm.js
asm2f = make_run('asm2f', emcc_args=['-Oz', '-s', 'PRECISE_F32=1', '-s', 'ALLOW_MEMORY_GROWTH=1', '-s', 'WASM=0'])
asm2nn = make_run('asm2nn', emcc_args=['-O2', '-s', 'WASM=0'], env={'EMCC_NATIVE_OPTIMIZER': '0'})

# wasm
binaryen2jo = make_run('binaryen2jo', emcc_args=['-O2', '-s', 'BINARYEN_METHOD="native-wasm,asmjs"'])
binaryen3jo = make_run('binaryen3jo', emcc_args=['-O3', '-s', 'BINARYEN_METHOD="native-wasm,asmjs"'])
binaryen2s = make_run('binaryen2s', emcc_args=['-O2', '-s', 'SAFE_HEAP=1'])
binaryen2_interpret = make_run('binaryen2_interpret', emcc_args=['-O2', '-s', 'BINARYEN_METHOD="interpret-binary"'])

# emterpreter
asmi = make_run('asmi', emcc_args=['-s', 'ASM_JS=2', '-s', 'EMTERPRETIFY=1', '-s', 'WASM=0'])
asm2i = make_run('asm2i', emcc_args=['-O2', '-s', 'EMTERPRETIFY=1', '-s', 'WASM=0'])

# TestCoreBase is just a shape for the specific subclasses, we don't test it itself
del TestCoreBase # noqa
