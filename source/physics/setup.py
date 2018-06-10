try:
    # for the dreaded error: Unable to find vcvarsall.bat
    # https://github.com/cython/cython/wiki/CythonExtensionsOnWindows
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension

from Cython.Build import cythonize

# python setup.py build_ext --inplace
setup(ext_modules = cythonize("physics_cython.pyx"))
