import sys

from Cython.Build import cythonize
from setuptools import Extension, setup

# MSVC (used by "distutils"-style builds on Windows) does not understand GCC/Clang
# style optimization flags such as "-O3".
if sys.platform == "win32":
    opt_args = ["/O2"]
else:
    opt_args = ["-O3"]

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
