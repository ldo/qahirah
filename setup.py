#+
# Distutils script to install qahirah. Invoke from the command line
# in this directory as follows:
#
#     python3 setup.py build
#     sudo python3 setup.py install
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import distutils.core

distutils.core.setup \
  (
    name = "Qahirah",
    version = "0.3",
    description = "language bindings for the Cairo graphics library, for Python 3.2 or later",
    author = "Lawrence D'Oliveiro",
    author_email = "ldo@geek-central.gen.nz",
    url = "http://github.com/ldo/qahirah",
    py_modules = ["qahirah"],
  )
