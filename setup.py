from setuptools import setup

import codecs
import os
import re
import versioneer


setup(
    name="chimedb.data_index",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=["chimedb.data_index"],
    zip_safe=False,
    install_requires=[
        "chimedb @ git+https://github.com/chime-experiment/chimedb.git",
        "peewee >= 3.10",
        "future",
        "h5py",
    ],
    author="CHIME collaboration",
    author_email="dvw@phas.ubc.ca",
    description="CHIME data index (alpenhorn) ORM",
    license="GPL v3.0",
    url="https://github.org/chime-experiment/chimedb_di",
)
