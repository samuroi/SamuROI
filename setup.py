from distutils.core import setup

setup(
    name='samuroi',
    packages=['samuroi'],
    version='0.1',
    license='MIT',
    description='Segmentation and Analysis of Multiple User-defined ROIs',
    author='Martin Rueckl',
    author_email='enigma@nbubu.de',
    url='https://github.com/aolsux/SamuROI',
    download_url='https://github.com/aolsux/SamuROI/tarball/0.1',
    keywords=['ROI', 'data exploration', 'image', 'segmentation', 'event detection'],
    classifiers=[],
    install_requires=[
        'numpy', 'h5py', 'scikit-image', 'matplotlib', 'pillow'
    ],
)
