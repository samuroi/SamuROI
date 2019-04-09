import sys

import numpy


def main():
    # only necessary from within scripts
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # samuroi imports
    from samuroi import SamuROIWindow

    # generate some random data, as the constructor needs a 3d array :-(
    data = numpy.random.normal(size=(300, 300, 300))

    # show the gui for the loaded data
    mainwindow = SamuROIWindow(data=data)

    # maybe necessary depending on IPython
    mainwindow.show()

    # only necessary in scripts
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
