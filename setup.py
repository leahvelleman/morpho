from setuptools import setup
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys
import morpho

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.rst')

setup(
    name='morpho',
    version=0.0, #morpho.__version__,
    url='http://github.com/leahvelleman/morpho/',
    license='Apache Software License',
    author='Leah Grace Velleman',
    install_requires=[ ],
    author_email='leahvelleman@gmail.com',
    description='',
    long_description=long_description,
    packages=['morpho'],
    include_package_data=True,
    platforms='any',
    #test_suite='sandman.test.test_sandman',
    classifiers = [ ],
    setup_requires = ['pytest-runner'],
    tests_require = ['pytest'],
)
