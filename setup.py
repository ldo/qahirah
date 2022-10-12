#+
# Setuptools script to install qahirah. Make sure setuptools
# <https://setuptools.pypa.io/en/latest/index.html> is installed.
# Invoke from the command line in this directory as follows:
#
#     python3 setup.py build
#     sudo python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import sys
import setuptools
from setuptools.command.build_py import \
    build_py as std_build_py

class my_build_py(std_build_py) :
    "customization of build to perform additional validation."

    def run(self) :
        try :
            import enum
            class dummy :
                pass
            #end dummy
            dummy.__doc__ = "something"
        except (ImportError, AttributeError) :
            sys.stderr.write("This module requires Python 3.4 or later.\n")
            sys.exit(-1)
        #end try
        super().run()
    #end run

#end my_build_py

setuptools.setup \
  (
    name = "Qahirah",
    version = "1.2",
    description = "language bindings for the Cairo graphics library, for Python 3.4 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "https://github.com/ldo/qahirah",
    py_modules = ["qahirah"],
    cmdclass =
        {
            "build_py" : my_build_py,
        },
  )
