#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="PyBLE",
      version="0.1",
      description="Python Bluetooth Smart(BLE) manager wrapper for OSX, Linux and Windows 8",
      author="Brett Chien",
      author_email="brett.chien@gmail.com",
      url="",
      packages=find_packages(exclude="tests"),
      )
