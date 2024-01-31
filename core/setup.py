from setuptools import setup, find_packages

# Function to read the contents of the requirements file
def read_requirements():
    with open('requirements.txt', 'r') as req:
        return req.read().splitlines()

setup(
    name='medium_parser',
    version='0.1.0',
    author='Freedium community',
    author_email='admin@freedium.cfd',
    description='A parser for Medium posts',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://codeberg.org/Freedium-cfd/web',
    packages=find_packages(),
    install_requires=read_requirements(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)