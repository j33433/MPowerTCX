#!/usr/bin/python
license = """\
 MPowerTCX: Share Schwinn A.C. indoor cycle data with Strava, GoldenCheetah and other apps
 Copyright (C) 2016 James Roth

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from datetime import datetime

from PySide.QtGui import *
from PySide.QtCore import *
from about import Ui_Dialog
from mainwindow import Ui_MainWindow
from mpower import MPower
import traceback

class About(QDialog, Ui_Dialog):
    """ Show license, version, etc """
    def __init__(self, version):
        super(About, self).__init__()
        self.setupUi(self)
        self.licenseEdit.appendPlainText(license)
        self.labelVersion.setText("Version: " + version)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.version = "v1.1.5"
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
        """ Put UI elements into their initial states """
        self.statusBar().showMessage(self.version)
        self.saveButton.setEnabled(False)
        self.workoutTime.setDateTime(datetime.now())

        use_file_date = self.settings.value(self.file_date_key, 'True')
        self.useFileDate.setChecked(use_file_date in [True, 'True', 'true'])

        include_speed = self.settings.value(self.include_speed_key, 'True')
        self.includeSpeedData.setChecked(include_speed in [True, 'True', 'true'])
        
        power_adjust = float(self.settings.value(self.power_adjust_key, 0.0))
        self.powerAdjustment.setValue(power_adjust)

    def assignWidgets(self):
        """ Connect signals to slots """
        self.useFileDate.stateChanged.connect(self.useFileDateChanged)
        self.includeSpeedData.stateChanged.connect(self.includeSpeedDataChanged)
        self.powerAdjustment.valueChanged.connect(self.powerAdjustmenChanged)
        self.loadButton.clicked.connect(self.loadPushed)
        self.saveButton.clicked.connect(self.savePushed)
        self.actionAbout.triggered.connect(self.showAbout)

    def alert(self, message):
        """ Simple alert box """
        box = QMessageBox()
        box.setText("MPowerTCX\n - %s" % message)
        box.exec_()

    def powerAdjustmenChanged(self, value):
        self.settings.setValue(self.power_adjust_key, value)
    
    def includeSpeedDataChanged(self, state):
        value = state == Qt.Checked
        self.settings.setValue(self.include_speed_key, value)
    
    def useFileDateChanged(self, state):
        """ The checkbox was clicked """
        value = state == Qt.Checked
        self.workoutTime.setEnabled(not value)
        self.settings.setValue(self.file_date_key, value)

    def showAbout(self):
        about = About(self.version)
        about.exec_()

    def loadPushed(self):
        """ Let the user select a CSV file. Load if possible. """
        csv_dir_key = "file/csv_dir"
        csv_dir = self.settings.value(csv_dir_key, ".")
        (filename, filter) = QFileDialog.getOpenFileName(self, "Open CSV", csv_dir, "CSV Files (*.csv);;All Files (*)")

        self.saveButton.setEnabled(False)
        self.labelDuration.setText("---")
        self.labelAveragePower.setText("---")
        self.labelMaxPower.setText("---")

        if filename:
            try:
                self.mpower = MPower(filename)
                self.mpower.load_csv()
            except Exception as error:
                oops = traceback.format_exc().splitlines()
                self.alert("\nThere was an error.\nPlease report this to j33433@gmail.com.\nInclude your file in the email.\n\n%s\n%s\n%s\n" % 
                    (oops[-3].strip(), oops[-2].strip(), oops[-1].strip()))
            else:
                header = self.mpower.header()

                if self.mpower.count():
                    self.alert("The CSV file was loaded successfully.")
                else:
                    self.alert("This file does not appear to contain ride data.")
                    return

                # Time to h:m:s
                m, s = divmod(int(header.time), 60)
                h, m = divmod(m, 60)

                self.saveButton.setEnabled(True)
                self.labelDuration.setText("%d:%02d:%02d" % (h, m, s))
                self.labelAveragePower.setText(str(header.average_power))
                self.labelMaxPower.setText(str(header.max_power))

            self.in_file_info = QFileInfo(filename)
            csv_dir = self.in_file_info.absoluteDir().path()
            self.settings.setValue(csv_dir_key, csv_dir)

    def savePushed(self):
        """ Let the user select a TCX file to save to. Store the data. """
        tcx_dir_key = "file/tcx_dir"
        tcx_dir = self.settings.value(tcx_dir_key, ".")
        use_file_date = self.useFileDate.isChecked()
        
        if use_file_date:
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
        

# Main logic
if len(sys.argv) == 3:
    # Run from the command line
    mpower = MPower(sys.argv[1])
    mpower.load_csv()
    mpower.save_data(sys.argv[2], datetime.now())
else:
    # Run from the UI
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit(ret)

