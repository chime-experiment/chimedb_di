from setuptools import setup, find_packages

from chimedb.data_index import __version__

setup(
    name='chimedb.data_index',
    version=__version__,

    packages=['chimedb.data_index'],
    zip_safe=False,

    install_requires=[
        'chimedb @ git+ssh://git@github.com/chime-experiment/chimedb.git',
        'peewee < 3', 'future'
    ],

    author="CHIME collaboration",
    author_email="dvw@phas.ubc.ca",
    description="CHIME data index (alpenhorn) ORM",
    license="GPL v3.0",
    url="https://github.org/chime-experiment/chimedb_di"
)
