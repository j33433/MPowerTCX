#
# Please note: setup_pyinstaller.bat produces a 10x smaller result. You probably
# want to run that instead.
#

# Example: python setup_cx_freeze.py build

import os
from cx_Freeze import setup, Executable
import version

import scipy
scipy_path = os.path.dirname(scipy.__file__)

options = {
    'build_exe': {
        'packages': ['numpy'],
        'excludes': ['scipy.spatial.cKDTree'],
        'includes': ['numpy.core._methods', 'numpy.lib.format', 
                     'scipy.sparse.csgraph._validation', 'scipy.special._ufuncs_cxx']
#        'include_files': [scipy_path, scipy_path + '/special/specfun.pyd']
    }
}

import sys
base = 'Win32GUI' if sys.platform=='win32' else None
#base = None

executables = [
    Executable('mpowertcx.py', base=base, icon='..\images\mpowertcx icon flat.ico')
]

setup(name='MPowerTCX',
      version = version.version,
      description = '',
      options = options,
      executables = executables)
