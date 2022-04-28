"""
    Interfaces for Githaxs Tasks

    Contact: hello@githaxs.com
"""
from setuptools import setup

NAME = "task_interfaces"
VERSION = "0.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["pydantic"]

setup(
    name=NAME,
    version=VERSION,
    install_requires=REQUIRES,
)
