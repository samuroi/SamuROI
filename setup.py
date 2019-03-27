from distutils.core import setup

setup(
    name='samuroi',
    packages=['samuroi'],
    version='0.1',
    license='MIT',
    description='Segmentation and Analysis of Multiple User-defined ROIs',
    author='Martin Rueckl',
    author_email='enigma@nbubu.de',
    url='https://github.com/samuroi/SamuROI',
    keywords=['ROI', 'data exploration', 'image', 'segmentation', 'event detection'],
    classifiers=[],
    install_requires=[
        'numpy>=1.16.2',
        'h5py>=2.9.0',
        'matplotlib>=3.0.0',
        'pillow>=5.4.1',
        'pyqt5>=5.12.1',
        'cached_property'
    ],
)
