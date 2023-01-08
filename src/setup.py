from pathlib import Path

import setuptools


ROOT_DIRECTORY = Path(__file__).parent.resolve()

setuptools.setup(
    name='tesstrain',
    description='Training utils for Tesseract',
    long_description=(ROOT_DIRECTORY / 'README.md').read_text(encoding='utf-8'),
    long_description_content_type='text/markdown',
    url='https://github.com/tesseract-ocr/tesstrain',
    packages=setuptools.find_packages(),
    license='Apache Software License 2.0',
    author='Tesseract contributors',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='Tesseract,tesseract-ocr,OCR,optical character recognition',

    python_requires='>=3.7',
    install_requires=[
        'tqdm',
    ],

    entry_points={
        'console_scripts': [
        ],
    },
)
