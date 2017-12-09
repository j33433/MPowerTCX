#
# This file builds the windows executable usig cx_freeze
#
# Example: pyhton setup.py build

import os
from cx_Freeze import setup, Executable

import scipy
scipy_path = os.path.dirname(scipy.__file__)

options = {
    'build_exe': {
        'packages': ['numpy'],
        'includes': ['numpy.core._methods', 'numpy.lib.format'],
        'include_files': scipy_path
    }
}

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('mpowertcx.py', base=base, icon='..\images\mpowertcx icon flat.ico')
]

setup(name='MPowerTCX',
      version = '1.0',
      description = '',
      options = options,
      executables = executables)
