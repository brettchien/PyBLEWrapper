#!/usr/bin/env python
from setuptools import setup, find_packages

import platform
system = platform.system()
requirements = []
if system == "Darwin":
    requirements.append("pyobjc-core")
    requirements.append("pyobjc-framework-Cocoa")
elif system == "Linux":
    pass
else:
    # windows
    pass

versionStr = "0.2.6"

setup(
        name="PyBLEWrapper",
        version=versionStr,
        #      description="Python Bluetooth Smart(BLE) manager wrapper for OSX, Linux and Windows 8",
        description="Python Bluetooth Smart(BLE) manager wrapper for OSX",
        author="Brett Chien",
        author_email="brett.chien@gmail.com",
        license="MIT",
        url="https://github.com/brettchien/PyBLEWrapper",
        download_url='https://github.com/brettchien/PyBLEWrapper/tarball/' + versionStr,
        packages=find_packages(exclude="tests"),
        install_requires=requirements,
        keywords = ['Bluetooth Low Energy', 'BLE', 'OSX'],
        classifiers = [],
        )

