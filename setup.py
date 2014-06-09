from setuptools import setup


setup(
    name="sqlitefts",
    version="0.2",
    packages=["sqlitefts"],
    description='A Python binding of SQLite Full Text Search Tokenizer',
    url='https://github.com/hideaki-t/igo-python/',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Database'
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    author='Hideaki Takahashi',
    author_email='mymelo@gmail.com',
    license='MIT',
    keywords=['SQLite', 'Full-text search', 'FTS'],
)
