from distutils.core import setup, Extension
from Cython.Build import cythonize

ext_module = Extension(
    "dynamic",
    ["dynamic.pyx"],
    language="c++",
    extra_compile_args=["-std=c++11", "-stdlib=libc++", "-mmacosx-version-min=10.9"],
    extra_link_args=["-std=c++11", "-mmacosx-version-min=10.9"]
) 

setup(
  name = 'Lillabo track solver',
  scripts = ['solver.py', 'track.py', 'collision.py'],
  ext_modules = cythonize(ext_module),
  data_files = ('data', ['data/*']),
)
