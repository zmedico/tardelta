
import sys

from setuptools import setup

sys.path.insert(0, "src")
from tardelta import (
    __author__,
    __email__,
    __project__,
    __version__,
)
sys.path.remove("src")

setup(
    name=__project__,
    version=__version__,
    description='tarball delta generator',
    author=__author__,
    author_email=__email__,
    package_dir={'': 'src'},
    py_modules=['tardelta'],
    entry_points={'console_scripts': 'tardelta = tardelta:main'},
)
