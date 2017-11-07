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

long_description = read('README.txt', 'CHANGES.txt')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='morpho',
    version=morpho.__version__,
    url='http://github.com/leahvelleman/morpho/',
    license='Apache Software License',
    author='Leah Grace Velleman',
    tests_require=['pytest'],
    install_requires=[ ],
    cmdclass={'test': PyTest},
    author_email='leahvelleman@gmail.com',
    description='',
    long_description=long_description,
    packages=['morpho'],
    include_package_data=True,
    platforms='any',
#    test_suite='sandman.test.test_sandman',
    classifiers = [ ],
    extras_require={
        'testing': ['pytest'],
    }
)
