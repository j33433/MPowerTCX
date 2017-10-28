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
    Executable('mpowertcx.py', base=base)
]

setup(name='MPowerTCX',
      version = '1.0',
      description = '',
      options = options,
      executables = executables)
