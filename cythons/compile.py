from distutils.core import setup
from Cython.Build import cythonize

setup(name = "my app", ext_modules = cythonize("functions.pyx"))
