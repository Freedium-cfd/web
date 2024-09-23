from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("server.__main__", ["server/__main__.pyx"]),
]

setup(
    ext_modules=cythonize(extensions),
)
