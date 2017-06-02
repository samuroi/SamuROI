[<img src="https://readthedocs.org/projects/samuroi/badge/?version=latest">](http://samuroi.readthedocs.io/en/latest/?badge=latest)

# SamuROI
You can find the API documentation and examples at: http://samuroi.readthedocs.io/en/latest/

## Installation
SamuROI installation was tested on:
 - Windows7-64bit, newer windows should also work.
 - Ubuntu 16.04 LTS
 
### Development installation with conda
 1. Download and install [anaconda](https://www.continuum.io/downloads) 
 2. Download and extract or git clone SamuROI
 3. Install dependencies
 
    Open a terminal to first install SamuROI dependencies. Text in `this font` represents terminal commands.
    - `conda install conda-build` 
    - `conda install pyqt=4` 
    - `conda install cached-property` 
    
    Finally, opencv does not ship official packages for all operation systems.
    On windows try `conda install -c menpo opencv=2.4.11`, on linux and mac try `conda install opencv`.
    If the opencv installation fails, SamuROI should still work, but the image stabilization will not be supported.
 4. Install SamuROI as a conda develop package: `conda develop <path/to/samuroi>`. Here <path/to/samuroi> denotes the samuroi root directory where you can e.g. find this Readme.md file.
    
### Via package manager (hopefully comming soon)
We hope to support a conda package soon! Contributions including a travis-ci setup are highly appreciated.
As there exist no official pip packages for opencv and pyqt, installation of SamuROI via pip is not officially supported.
