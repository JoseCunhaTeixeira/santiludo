import sys

from Cython.Build import cythonize
from setuptools import Extension, setup

# MSVC (used by "distutils"-style builds on Windows) does not understand GCC/Clang
# style optimization flags such as "-O3". The C++ sources use std::string_view
# (C++17), so the standard must be requested explicitly: MSVC defaults to C++14,
# and while most GCC/Clang versions in use default to C++17 or later, it's not
# guaranteed, so pin it there too.
if sys.platform == "win32":
    opt_args = ["/O2", "/std:c++17"]
else:
    opt_args = ["-O3", "-std=c++17"]

CPP_DIR = "src/santiludo/_cpp"

extensions = [
    Extension(
        "santiludo.VGfunctions",
        [f"{CPP_DIR}/VGfunctions.pyx"],
        language="c++",
        extra_compile_args=opt_args,
        extra_link_args=opt_args,
    ),
    Extension(
        "santiludo.RPfunctions",
        [f"{CPP_DIR}/RPfunctions.pyx", f"{CPP_DIR}/VGfunctions_src.cpp"],
        language="c++",
        extra_compile_args=opt_args,
        extra_link_args=opt_args,
    ),
    Extension(
        "santiludo.TTDSPfunctions",
        [f"{CPP_DIR}/TTDSPfunctions.pyx"],
        language="c++",
        extra_compile_args=opt_args,
        extra_link_args=opt_args,
    ),
]

setup(
    ext_modules=cythonize(extensions, language_level=3),
)
