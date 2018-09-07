from setuptools import setup


setup(
    name='petriish',
    version='0.1.0',
    description='Hierarchical workflow engine',
    license='MIT',
    url='https://github.com/SupraSummus/petriish',
    classifiers=[
        'Operating System :: POSIX',
        'Topic :: System',
        'Topic :: Utilities',
    ],
    keywords='petri workflow',
    py_modules=['petriish'],
    scripts=[
        'bin/petriish',
    ],
    install_requires=[
        'pyyaml',
    ],
)
