# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt').read().split('\n')

setup(
    name='tesstrain-python',
    version='0.0.1',
    description='tesstrain helpers',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='tesstrain community',
    author_email='info@ocr-d.de',
    url='https://github.com/tesseract-ocr/tesstrain',
    license='Apache License 2.0',
    packages=['generate_sets'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'tesstrain-extract-gt=generate_sets.cli:main',
        ]
    },
)
