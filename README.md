[<img src="https://readthedocs.org/projects/samuroi/badge/?version=latest">](http://samuroi.readthedocs.io/en/latest/?badge=latest)

# SamuROI
If you use this software, please cite:
You can find the documentation at: http://samuroi.readthedocs.io/en/latest/

## Requirements
SamuROI requires the following python packages:
- python
- numpy
- matplotlib
- cached-property
- opencv
- h5py
- scikit-image
- pyqt4 (make sure to tell conda to install pyqt4 via `conda install pyqt=4` )
- pillow

## Installation
### From source with conda (recommended)
 1. Install the requirements listed above with the conda package manager:
 
  `conda install <dependency>`
 2. Clone SamuROI git repository:
 
  `git clone https://github.com/aolsux/SamuROI.git`
 3. Tell conda about the downloaded git repository. This will e.g. add the source directory to python path.
 
    `conda develop /path/to/local/git/repo`
    
    Unless you haven't specified a special directory for git to clone into, your `/path/to/local/git/repo` will just be `.SamuROI`.

### Via conda package manager (hopefully comming soon)
It is recommended to install SamuROI via the conda package manager, 
since conda comes with packages for scikit-image, opencv and pyqt.
`conda install samuroi`

## Installation via pip
To install SamuROI via pip make sure to satisfy the following dependencies
manually:
- opencv
- scikit-image
- pyqt
