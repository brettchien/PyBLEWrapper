#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="PyBLE",
      version="0.2.2",
#      description="Python Bluetooth Smart(BLE) manager wrapper for OSX, Linux and Windows 8",
      description="Python Bluetooth Smart(BLE) manager wrapper for OSX",
      author="Brett Chien",
      author_email="brett.chien@gmail.com",
      url="",
      packages=find_packages(exclude="tests"),
      )
