#!/bin/env python
from setuptools import setup, find_packages

setup(
    name='samuroi',
    version='0.1',
    license='MIT',
    description='Segmentation and Analysis of Multiple User-defined ROIs',
    author='Martin Rueckl',
    author_email='enigma@nbubu.de',
    url='https://github.com/samuroi/SamuROI',
    keywords=['ROI', 'data exploration', 'image', 'segmentation', 'event detection'],
    classifiers=[],
    python_requires='>=3.6.*',
    packages=find_packages(exclude=("test", "test.*")),
    install_requires=[
        'numpy>=1.16.2',
        'scipy>=1.2.1',
        'h5py>=2.9.0',
        'matplotlib>=3.0.0',
        'pillow>=5.4.1',
        'pyqt5>=5.12.1',
        'scikit-image>=0.14.2',
        'cached_property',
    ],
    extras_require={
        'stabilize': ["opencv-python>=4.0.0"]
    },
    # generate a samuroi "executable" that runs the main method.
    entry_points={
        'console_scripts': [
            'samuroi = samuroi:main.main',
        ],
    }
)
