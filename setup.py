# -*- coding: utf-8 -*-
from setuptools import setup

install_requires = open('requirements.txt', encoding='utf-8').read().split('\n')

setup(
    name='tesstrain-python',
    version='0.0.1',
    description='tesstrain helpers',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='tesstrain community',
    author_email='info@ocr-d.de',
    url='https://github.com/tesseract-ocr/tesstrain',
    license='Apache License 2.0',
    packages=['extract_sets'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'tesstrain-extract-sets=extract_sets.cli:main',
        ]
    },
)
