from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'Lillabo track solver',
  scripts = ['solver.py'],
  ext_modules = cythonize("dynamic.pyx"),
)
