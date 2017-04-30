#+
# Distutils script to install qahirah. Invoke from the command line
# in this directory as follows:
#
#     python3 setup.py build
#     sudo python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import sys
import distutils.core
from distutils.command.build import \
    build as std_build

class my_build(std_build) :
    "customization of build to perform additional validation."

    def run(self) :
        try :
            class dummy :
                pass
            #end dummy
            dummy.__doc__ = "something"
        except AttributeError :
            sys.stderr.write("This module requires Python 3.3 or later.\n")
            sys.exit(-1)
        #end try
        super().run()
    #end run

#end my_build

distutils.core.setup \
  (
    name = "Qahirah",
    version = "0.9",
    description = "language bindings for the Cairo graphics library, for Python 3.3 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "http://github.com/ldo/qahirah",
    py_modules = ["qahirah"],
    cmdclass =
        {
            "build" : my_build,
        },
  )
