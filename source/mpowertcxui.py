import platform
import sys
import threading
import traceback
from datetime import datetime

from dateutil import tz
from PySide2.QtCore import QSettings, QFileInfo
from PySide2.QtGui import Qt, QIcon
from PySide2.QtWidgets import QDialog, QMainWindow, QMessageBox, QFileDialog, QApplication

import version
from mpower import MPower
from widgetsettings import WidgetSettings

license = """\
 MPowerTCX: Share Schwinn A.C. indoor cycle data with Strava,
 GoldenCheetah and other apps.

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

#
# This file contains the GUI logic
#


if sys.version_info[0] < 3:
    raise Exception("python 3 is required")

if platform.system() == 'Darwin':
    # The UIC generates things differently for the OS X context menu
    from ui.about_Darwin import Ui_Dialog
    from ui.mainwindow_Darwin import Ui_MainWindow
else:
    from ui.about import Ui_Dialog
    from ui.mainwindow import Ui_MainWindow


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
        self.version = version.version
        self.trues = [True, 'True', 'true']  # workaround for pyside
        self.setupUi(self)
#        self.menuHelp.menuAction().setMenuRole(QAction.AboutRole)
#        self.menuBar().setMenuRole(QAction.AboutRole)
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
        self.labelEquipment.setText("---")

        if filename:
            try:
                self.mpower = MPower(filename)
                self.mpower.load_csv()
            except Exception:
                oops = traceback.format_exc().splitlines()
                self.alert("\nThere was an error."
                           "\nPlease report this to j33433@gmail.com."
                           "\nInclude your file in the email."
                           "\n\nVersion %s"
                           "\n\n%s\n%s\n%s\n" %
                           (version.version, oops[-3].strip(), oops[-2].strip(), oops[-1].strip()))
            else:
                header = self.mpower.header()

                if self.mpower.count():
                    # Time to h:m:s
                    m, s = divmod(int(header.time), 60)
                    h, m = divmod(m, 60)

                    self.saveButton.setEnabled(True)
                    self.labelDuration.setText("%d:%02d:%02d" % (h, m, s))
                    self.labelAveragePower.setText(str(header.average_power))
                    self.labelMaxPower.setText(str(header.max_power))
                    self.labelEquipment.setText(header.equipment)
                    self.alert("The CSV file was loaded successfully.")
                else:
                    self.alert("This file does not appear to contain ride data.")
                    return

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
        self.saveButton.setEnabled(False)
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
        self.alert(thread_result['message'])

        info = QFileInfo(filename)
        tcx_dir = info.absoluteDir().path()
        self.settings.setValue(tcx_dir_key, tcx_dir)


def runui():
    dont_free = []
    QApplication.setStyle('Cleanlooks')
    app = QApplication(sys.argv)
    icon = QIcon(':/icon/mpowertcx icon flat.png')
    app.setWindowIcon(icon)
    mainWin = MainWindow()
    dont_free.append(mainWin)
    ret = app.exec_()
    sys.exit(ret)
