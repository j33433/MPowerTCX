#!/usr/bin/python

import sys
from datetime import datetime

from PySide.QtGui import *
from PySide.QtCore import *
from mainwindow import Ui_MainWindow
from mpower import MPower


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.configure()
        self.assignWidgets()
        self.show()

    def configure(self):
        self.workoutTime.setDateTime(datetime.now())

    def assignWidgets(self):
        self.loadButton.clicked.connect(self.loadPushed)
        self.saveButton.clicked.connect(self.savePushed)
        self.saveButton.setEnabled(False)

    def loadPushed(self):
        print ("load")

    def savePushed(self):
        print ("save")

app = QApplication(sys.argv)
mainWin = MainWindow()
ret = app.exec_()
sys.exit(ret)

#mpower = MPower(sys.argv[1], sys.argv[2])
#mpower.process()

