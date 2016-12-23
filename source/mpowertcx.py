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
        self.file_date_key = "use_file_date"
        self.setupUi(self)
        self.assignWidgets()
        self.configure()
        self.show()
        self.mpower = None
        self.in_file_info = None

    def configure(self):
        self.workoutTime.setDateTime(datetime.now())

        use_file_date = self.settings.value(self.file_date_key, "True")
        self.useFileDate.setChecked(use_file_date in ['True', 'true'])

        include_speed = self.settings.value(self.include_speed_key, "True")
        self.includeSpeedData.setChecked(include_speed in ['True', 'true'])

        power_adjust = float(self.settings.value(self.power_adjust_key, 0.0))
        self.powerAdjustment.setValue(power_adjust)

    def assignWidgets(self):
        self.useFileDate.stateChanged.connect(self.useFileDateChanged)
        self.loadButton.clicked.connect(self.loadPushed)
        self.saveButton.clicked.connect(self.savePushed)
        self.saveButton.setEnabled(False)

    def alert(self, message):
        box = QMessageBox()
        box.setText("MPowerTCX\n - %s" % message)
        box.exec_()

    def useFileDateChanged(self, state):
        self.workoutTime.setEnabled(state != Qt.Checked)
        print ("state %r" % state)

    def loadPushed(self):
        csv_dir_key = "file/csv_dir"
        csv_dir = self.settings.value(csv_dir_key, ".")
        (filename, filter) = QFileDialog.getOpenFileName(self, "Open CSV", csv_dir, "CSV Files (*.csv);;All Files (*)")

        self.saveButton.setEnabled(False)
        self.labelDuration.setText("---")
        self.labelAveragePower.setText("---")
        self.labelMaxPower.setText("---")

        if filename:
            print (filename)

            try:
                self.mpower = MPower(filename)
                self.mpower.load_csv()
            except Exception as error:
                self.alert("There was an error: %s" % error)
            else:
                header = self.mpower.header()

                m, s = divmod(int(header.time), 60)
                h, m = divmod(m, 60)

                if self.mpower.count():
                    self.alert("The CSV file was loaded successfully.")
                else:
                    self.alert("This file does not appear to contain ride data.")
                    return

                self.saveButton.setEnabled(True)
                self.labelDuration.setText("%d:%02d:%02d" % (h, m, s))
                self.labelAveragePower.setText(str(header.average_power))
                self.labelMaxPower.setText(str(header.max_power))

            self.in_file_info = QFileInfo(filename)
            csv_dir = self.in_file_info.absoluteDir().path()
            self.settings.setValue(csv_dir_key, csv_dir)

    def savePushed(self):
        tcx_dir_key = "file/tcx_dir"
        tcx_dir = self.settings.value(tcx_dir_key, ".")

        if self.useFileDate.isChecked():
            start_time = self.in_file_info.created().toPython()
        else:
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
            self.alert("There was an error: %s" % error)
        else:
            self.alert("The TCX file was saved successfully.")

        info = QFileInfo(filename)
        tcx_dir = info.absoluteDir().path()
        self.settings.setValue(tcx_dir_key, tcx_dir)
        self.settings.setValue(self.include_speed_key, include_speed)
        self.settings.setValue(self.power_adjust_key, power_adjust)

if len(sys.argv) == 3:
    mpower = MPower(sys.argv[1])
    mpower.load_csv()
    mpower.save_data(sys.argv[2], datetime.now())
else:
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit(ret)

