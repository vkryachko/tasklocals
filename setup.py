import sys
from setuptools import setup, find_packages

install_requires = ['asyncio'] if sys.version_info[:2] < (3, 4) else []
tests_require = install_requires + ['nose']

setup(
    name="tasklocals",
    version="0.2",
    author = "Vladimir Kryachko",
    author_email = "v.kryachko@gmail.com",
    description = "Task locals for Tulip/asyncio",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],
    packages=['tasklocals'],
    install_requires = install_requires,
    tests_require = tests_require,
    test_suite = 'nose.collector',
)
