from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize


def read_requirements():
    with open("requirements.txt", "r") as req:
        return req.read().splitlines()


cython_extension_src = "rl_string_helper/mixins/string_assignment.pyx"
cython_extensions = [Extension("rl_string_helper.mixins.string_assignment", [cython_extension_src])]
# cython_extensions = ["rl_string_helper/test.pyx"]

setup(
    name="rl_string_helper",
    version="0.1.0",
    author="Freedium community",
    author_email="admin@freedium.cfd",
    description="Helper for Medium parser backend",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://codeberg.org/Freedium-cfd/web",
    packages=find_packages(),
    install_requires=read_requirements(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    ext_modules=cythonize(cython_extensions, force=True, show_all_warnings=True),
    python_requires=">=3.7",
    zip_safe=False,
    include_package_data=True,
)
