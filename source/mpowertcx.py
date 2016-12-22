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
        self.settings = QSettings("j33433", "MPowerTCX")
        self.include_speed_key = "include_speed"
        self.power_adjust_key = "power_adjust"
        self.setupUi(self)
        self.assignWidgets()
        self.configure()
        self.show()
        self.mpower = None
        self.in_file_info = None

    def configure(self):
        self.workoutTime.setDateTime(datetime.now())
        include_speed = self.settings.value(self.include_speed_key, "True")
        self.includeSpeedData.setChecked(include_speed in ['True', 'true'])
        power_adjust = float(self.settings.value(self.power_adjust_key, 0.0))
        self.powerAdjustment.setValue(power_adjust)

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
                self.saveButton.setEnabled(True)

            self.in_file_info = QFileInfo(filename)
            csv_dir = self.in_file_info.absoluteDir().path()
            self.settings.setValue(csv_dir_key, csv_dir)

    def savePushed(self):
        tcx_dir_key = "file/tcx_dir"
        tcx_dir = self.settings.value(tcx_dir_key, ".")
        start_time = self.workoutTime.dateTime().toPython()

        dialog = QFileDialog(self)
        dialog.selectFile(self.in_file_info.baseName() + ".tcx")
        dialog.setDirectory(tcx_dir)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        filename = None

        if dialog.exec_():
            filenames = dialog.selectedFiles()

            if len(filenames):
                filename = filenames[0]

        if not filename:
            # User cancel
            return

        include_speed = self.includeSpeedData.isChecked()
        power_adjust = self.powerAdjustment.value()
        self.mpower.set_include_speed_data(include_speed)
        self.mpower.set_power_adjust(power_adjust)

        try:
            self.mpower.save_data(filename, start_time)
        except Exception as error:
            print ("got an error")
        else:
            print ("ok")

        info = QFileInfo(filename)
        tcx_dir = info.absoluteDir().path()
        self.settings.setValue(tcx_dir_key, tcx_dir)
        self.settings.setValue(self.include_speed_key, include_speed)
        self.settings.setValue(self.power_adjust_key, power_adjust)

app = QApplication(sys.argv)
mainWin = MainWindow()
ret = app.exec_()
sys.exit(ret)

#mpower = MPower(sys.argv[1], sys.argv[2])
#mpower.process()

