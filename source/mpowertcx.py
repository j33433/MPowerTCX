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
        self.mpower = None
        self.settings = QSettings("j33433", "MPowerTCX")
        self.in_file_info = None

    def configure(self):
        self.workoutTime.setDateTime(datetime.now())

    def assignWidgets(self):
        self.loadButton.clicked.connect(self.loadPushed)
        self.saveButton.clicked.connect(self.savePushed)
        self.saveButton.setEnabled(False)

    def loadPushed(self):
        csv_dir_key = "file/csv_dir"
        csv_dir = self.settings.value(csv_dir_key, ".")
        (filename, filter) = QFileDialog.getOpenFileName(self, "Open CSV", csv_dir, "CSV Files (*.csv)")
        self.saveButton.setEnabled(False)

        if filename:
            print (filename)

            try:
                self.mpower = MPower(filename)
                self.mpower.load_csv()
            except Exception as error:
                print ("got an error")
            else:
                print ("ok")
                self.saveButton.setEnabled(True)

            self.in_file_info = QFileInfo(filename)
            csv_dir = self.in_file_info.absoluteDir().path()
            self.settings.setValue(csv_dir_key, csv_dir)

    def savePushed(self):
        tcx_dir_key = "file/tcx_dir"
        tcx_dir = self.settings.value(tcx_dir_key, ".")
        start_time = self.workoutTime.dateTime().toPython()
        (filename, filter) = QFileDialog.getSaveFileName(self, "Open TCX", tcx_dir, "TCX Files (*.tcx)")

        print ("start time %r" % start_time)

        try:
            self.mpower.save_data(filename, start_time)
        except Exception as error:
            print ("got an error")
        else:
            print ("ok")

        info = QFileInfo(filename)
        tcx_dir = info.absoluteDir().path()
        self.settings.setValue(tcx_dir_key, tcx_dir)

app = QApplication(sys.argv)
mainWin = MainWindow()
ret = app.exec_()
sys.exit(ret)

#mpower = MPower(sys.argv[1], sys.argv[2])
#mpower.process()

