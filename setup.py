#!/usr/bin/env python3

# from distutils.core import setup
from setuptools import setup
setup(
    name='indesign-scripture-index',
    version='0.1',
    package_dir={'': 'src'},
    packages=['bible_lib'],
    requires=['fire', 'dataclasses', 'jinja2'],
    url='',
    license='GPL 2.0',
    author='John R. Supplee',
    author_email='john@elsoora.org',
    description='Create Scripture Reference Indices for InDesign documents',
    scripts=[
        'src/make-scripture-index',
    ]
)
