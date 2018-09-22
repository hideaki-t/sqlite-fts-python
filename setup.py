import sys
from setuptools import setup

setup(
    name="sqlitefts",
    version="0.5.1",
    packages=["sqlitefts"],
    description='A Python binding for tokenizers of SQLite Full Text Search',
    long_description=open('README.rst').read(),
    url='https://github.com/hideaki-t/sqlite-fts-python/',
    classifiers=[
        'Development Status :: 3 - Alpha', 'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    author='Hideaki Takahashi',
    author_email='mymelo@gmail.com',
    license='MIT',
    keywords=['SQLite', 'Full-text search', 'FTS'],
    install_requires=['cffi'],
)
