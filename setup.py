import os
import re
import subprocess
import sys

from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion


with open('README.md', 'r') as readme_file:
    long_description = readme_file.read()


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError(
                'CMake must be installed to build the following extensions: ' +
                ', '.join(e.name for e in self.extensions)
            )

        cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
        if cmake_version < LooseVersion('3.10.0'):
            raise RuntimeError('CMake >= 3.10.0 is required')

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        build_type = os.environ.get('BUILD_TYPE', 'Release')
        build_args = ['--config', build_type]

        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
            '-DPYTHON_EXECUTABLE={}'.format(sys.executable),
            '-DEXAMPLE_VERSION_INFO={}'.format(self.distribution.get_version()),
            '-DCMAKE_BUILD_TYPE=' + build_type,
            '-DUSE_PYTHON_EXTENSION=OFF',
            '-DBUILD_EXAMPLES=OFF',
            '-DBUILD_TESTS=OFF',
            '-DBUILD_SHARED_LIBS=OFF',
            '-DCMAKE_BUILD_WITH_INSTALL_RPATH=TRUE',
            '-DCMAKE_INSTALL_RPATH={}'.format('$ORIGIN'),
            '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
        ]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp)
        subprocess.check_call(['cmake', '--build', '.', '--target', ext.name] + build_args, cwd=self.build_temp)


setup(
    name='frankx',
    version='0.1.1',
    description='High-Level Motion Library for the Franka Panda Robot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Lars Berscheid',
    author_email='lars.berscheid@kit.edu',
    url='https://github.com/pantor/frankx',
    packages=find_packages(),
    license='LGPL',
    ext_modules=[CMakeExtension('_frankx'), CMakeExtension('pyaffx'), CMakeExtension('_movex')],
    cmdclass=dict(build_ext=CMakeBuild),
    keywords=['robot', 'robotics', 'trajectory-generation', 'motion-control'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: C++',
    ],
    python_requires='>=3.6',
    zip_safe=False,
)
