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

import os
import sys
import argparse
import platform
import threading

from datetime import datetime
import dateutil.parser

from PySide.QtGui import *
from PySide.QtCore import *
from ui.about import Ui_Dialog
from ui.mainwindow import Ui_MainWindow
from mpower import MPower
from dateutil import tz
from widgetsettings import WidgetSettings

import traceback

class About(QDialog, Ui_Dialog):
    """ 
    Show license, version, etc 
    """
    def __init__(self, version):
        super(About, self).__init__()
        self.setupUi(self)
        self.licenseEdit.appendPlainText(license)
        self.labelVersion.setText("Version: " + version)

class MainWindow(QMainWindow, Ui_MainWindow, WidgetSettings):
    lbs_to_kg = 0.453592
    
    def __init__(self):
        super(MainWindow, self).__init__()
        self.settings = QSettings("j33433", "MPowerTCX")
        WidgetSettings.__init__(self, self, 'settings.json', self.settings)
        self.version = "v2.0.1"
        self.trues = [True, 'True', 'true'] # workaround for pyside
        self.setupUi(self)
        self.unstash()
        self.assignWidgets()
        self.configure()
        self.show()
        self.mpower = None
        self.in_file_info = None
        self.resize(self.width(), self.minimumSizeHint().height())

    def configure(self):
        """ 
        Put UI elements into their initial states 
        """
        self.statusBar().showMessage(self.version)
        self.saveButton.setEnabled(False)
        self.workoutTime.setDateTime(datetime.now())

        hide = not self.checkBoxExtra.isChecked()
        self.groupBoxPhysics.setHidden(hide)
        self.groupBoxCompatibility.setHidden(hide)
        
    def assignWidgets(self):
        """ 
        Connect signals to slots 
        """
        self.useFileDate.stateChanged.connect(self.useFileDateChanged)
        self.checkBoxExtra.stateChanged.connect(self.checkBoxExtraChanged)
        
        self.powerAdjustment.valueChanged.connect(self.somethingChanged)
        self.comboBoxUnits.currentIndexChanged.connect(self.somethingChanged)
        self.checkBoxPhysics.stateChanged.connect(self.somethingChanged)
        self.checkBoxInterpolate.stateChanged.connect(self.somethingChanged)
        self.doubleSpinBoxRiderWeight.valueChanged.connect(self.somethingChanged)
        self.doubleSpinBoxBikeWeight.valueChanged.connect(self.somethingChanged)
        
        self.loadButton.clicked.connect(self.loadPushed)
        self.saveButton.clicked.connect(self.savePushed)
        self.actionAbout.triggered.connect(self.showAbout)

    def alert(self, message):
        """ 
        Simple alert box 
        """
        box = QMessageBox()
        box.setText("MPowerTCX\n - %s" % message)
        box.exec_()

    def somethingChanged(self, value):
        self.stash()

    def checkBoxExtraChanged(self, state):
        value = state == Qt.Checked
        self.groupBoxPhysics.setHidden(not value)
        self.groupBoxCompatibility.setHidden(not value)
        self.resize(self.width(), self.minimumSizeHint().height())
        self.stash()
        
    def useFileDateChanged(self, state):
        value = state == Qt.Checked
        self.workoutTime.setEnabled(not value)
        self.stash()

    def showAbout(self):
        about = About(self.version)
        about.exec_()

    def loadPushed(self):
        """ 
        Let the user select a CSV file. Load if possible. 
        """
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

    def saveThread(self, filename, start_time, result):
        try:
            self.mpower.save_data(filename, start_time)
        except Exception as error:
            oops = traceback.format_exc().splitlines()
            result['message'] = 'There was an error: %s\n\n%s\n%s\n%s\n' % (error, oops[-3].strip(), oops[-2].strip(), oops[-1].strip())
            result['status'] = False
        else:
            result['message'] = 'The TCX file was saved successfully.'
            result['status'] = True
        
    def savePushed(self):
        """ 
        Let the user select a TCX file to save to. Store the data. 
        """
        tcx_dir_key = "file/tcx_dir"
        tcx_dir = self.settings.value(tcx_dir_key, ".")
        use_file_date = self.useFileDate.isChecked()
        
        if use_file_date:
            local_time = self.in_file_info.created().toPython()
        else:
            local_time = self.workoutTime.dateTime().toPython()
        
        utc_zone = tz.tzutc()
        local_zone = tz.tzlocal()
        local_time = local_time.replace(tzinfo=local_zone)
        start_time = local_time.astimezone(utc_zone)

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

        power_adjust = self.powerAdjustment.value()
        self.mpower.set_power_adjust(power_adjust)
        self.mpower.set_interpolation(self.checkBoxInterpolate.isChecked())
        
        mass = self.doubleSpinBoxRiderWeight.value() + self.doubleSpinBoxBikeWeight.value()
        
        if self.comboBoxUnits.currentText() == "lbs":
            mass *= self.lbs_to_kg
        
        self.mpower.set_physics(self.checkBoxPhysics.isChecked(), mass)
 
        thread_result = {'message': None, 'status': False}
        t = threading.Thread(target=self.saveThread, args=(filename, start_time, thread_result))
        t.start()
        t.join()
        print (thread_result)
        self.alert(thread_result['message'])

        info = QFileInfo(filename)
        tcx_dir = info.absoluteDir().path()
        self.settings.setValue(tcx_dir_key, tcx_dir)


if len(sys.argv) == 1:
    # Run from the UI
    if platform.system() == 'Linux':
        QApplication.setStyle('Cleanlooks')
        
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    ret = app.exec_()
    sys.exit(ret)
else:
    # Run from the command line
    parser = argparse.ArgumentParser(description='Share indoor cycle data with Strava, Golden Cheetah and other apps')
    parser.add_argument('--csv', help='the spin bike file', required=True)
    parser.add_argument('--tcx', help='the output file', required=True)
    parser.add_argument('--time', help='the workout starting time')
    parser.add_argument('--interpolate', help='produce samples at one second intervals', action='store_true')
    parser.add_argument('--model', help='use physics model for speed and distance', metavar='MASS_KG')
    args = parser.parse_args()
    print(args)
    mpower = MPower(args.csv)
    mpower.load_csv()
    
    if args.time is not None:
        stamp = dateutil.parser.parse(args.time)
    else:
        # Take input file time
        stamp = datetime.fromtimestamp(os.path.getmtime(args.csv))
    
    if args.model is not None:
        mpower.set_physics(True, float(args.model))
    
    mpower.set_interpolation(args.interpolate)   
    mpower.save_data(args.tcx, stamp)
