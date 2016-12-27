#
# MPowerTCX: Share Schwinn A.C. indoor cycle data with Strava, GoldenCheetah and other apps
# Copyright (C) 2016 James Roth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created: Tue Dec 27 11:01:10 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(507, 288)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_3 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setObjectName("widget")
        self.gridLayout_4 = QtGui.QGridLayout(self.widget)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.loadButton = QtGui.QPushButton(self.widget)
        self.loadButton.setObjectName("loadButton")
        self.gridLayout_4.addWidget(self.loadButton, 0, 0, 1, 1)
        self.saveButton = QtGui.QPushButton(self.widget)
        self.saveButton.setObjectName("saveButton")
        self.gridLayout_4.addWidget(self.saveButton, 0, 1, 1, 1)
        self.gridLayout_3.addWidget(self.widget, 3, 1, 1, 3)
        self.groupBox_2 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.labelDurationName = QtGui.QLabel(self.groupBox_2)
        self.labelDurationName.setObjectName("labelDurationName")
        self.gridLayout_2.addWidget(self.labelDurationName, 0, 0, 1, 1)
        self.labelDuration = QtGui.QLabel(self.groupBox_2)
        self.labelDuration.setObjectName("labelDuration")
        self.gridLayout_2.addWidget(self.labelDuration, 0, 1, 1, 1)
        self.labelAveragePowerName = QtGui.QLabel(self.groupBox_2)
        self.labelAveragePowerName.setObjectName("labelAveragePowerName")
        self.gridLayout_2.addWidget(self.labelAveragePowerName, 1, 0, 1, 1)
        self.labelAveragePower = QtGui.QLabel(self.groupBox_2)
        self.labelAveragePower.setObjectName("labelAveragePower")
        self.gridLayout_2.addWidget(self.labelAveragePower, 1, 1, 1, 1)
        self.labelMaxPowerName = QtGui.QLabel(self.groupBox_2)
        self.labelMaxPowerName.setObjectName("labelMaxPowerName")
        self.gridLayout_2.addWidget(self.labelMaxPowerName, 2, 0, 1, 1)
        self.labelMaxPower = QtGui.QLabel(self.groupBox_2)
        self.labelMaxPower.setObjectName("labelMaxPower")
        self.gridLayout_2.addWidget(self.labelMaxPower, 2, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 1, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem, 1, 4, 1, 1)
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.labelWorkoutTime = QtGui.QLabel(self.groupBox)
        self.labelWorkoutTime.setObjectName("labelWorkoutTime")
        self.gridLayout.addWidget(self.labelWorkoutTime, 0, 0, 1, 1)
        self.workoutTime = QtGui.QDateTimeEdit(self.groupBox)
        self.workoutTime.setObjectName("workoutTime")
        self.gridLayout.addWidget(self.workoutTime, 0, 1, 1, 1)
        self.labelPowerAdjustment = QtGui.QLabel(self.groupBox)
        self.labelPowerAdjustment.setObjectName("labelPowerAdjustment")
        self.gridLayout.addWidget(self.labelPowerAdjustment, 2, 0, 1, 1)
        self.powerAdjustment = QtGui.QDoubleSpinBox(self.groupBox)
        self.powerAdjustment.setMinimum(-100.0)
        self.powerAdjustment.setMaximum(100.0)
        self.powerAdjustment.setSingleStep(0.1)
        self.powerAdjustment.setObjectName("powerAdjustment")
        self.gridLayout.addWidget(self.powerAdjustment, 2, 1, 1, 1)
        self.includeSpeedData = QtGui.QCheckBox(self.groupBox)
        self.includeSpeedData.setChecked(True)
        self.includeSpeedData.setObjectName("includeSpeedData")
        self.gridLayout.addWidget(self.includeSpeedData, 3, 0, 1, 2)
        self.useFileDate = QtGui.QCheckBox(self.groupBox)
        self.useFileDate.setObjectName("useFileDate")
        self.gridLayout.addWidget(self.useFileDate, 1, 0, 1, 2)
        self.gridLayout_3.addWidget(self.groupBox, 1, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem1, 2, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem2, 1, 0, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem3, 1, 2, 1, 1)
        spacerItem4 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem4, 4, 1, 1, 1)
        spacerItem5 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem5, 0, 2, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 507, 27))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QtGui.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionAbout = QtGui.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MPowerTCX", None, QtGui.QApplication.UnicodeUTF8))
        self.loadButton.setText(QtGui.QApplication.translate("MainWindow", "Load CSV...", None, QtGui.QApplication.UnicodeUTF8))
        self.saveButton.setText(QtGui.QApplication.translate("MainWindow", "Save TCX...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("MainWindow", "Statistics", None, QtGui.QApplication.UnicodeUTF8))
        self.labelDurationName.setText(QtGui.QApplication.translate("MainWindow", "Duration:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelDuration.setText(QtGui.QApplication.translate("MainWindow", "---", None, QtGui.QApplication.UnicodeUTF8))
        self.labelAveragePowerName.setText(QtGui.QApplication.translate("MainWindow", "Average Power:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelAveragePower.setText(QtGui.QApplication.translate("MainWindow", "---", None, QtGui.QApplication.UnicodeUTF8))
        self.labelMaxPowerName.setText(QtGui.QApplication.translate("MainWindow", "Max Power:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelMaxPower.setText(QtGui.QApplication.translate("MainWindow", "---", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.labelWorkoutTime.setText(QtGui.QApplication.translate("MainWindow", "Workout Time:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelPowerAdjustment.setText(QtGui.QApplication.translate("MainWindow", "Power Adjustment:", None, QtGui.QApplication.UnicodeUTF8))
        self.powerAdjustment.setSuffix(QtGui.QApplication.translate("MainWindow", "%", None, QtGui.QApplication.UnicodeUTF8))
        self.includeSpeedData.setText(QtGui.QApplication.translate("MainWindow", "Include Speed Data", None, QtGui.QApplication.UnicodeUTF8))
        self.useFileDate.setText(QtGui.QApplication.translate("MainWindow", "Use File Time as Workout Time", None, QtGui.QApplication.UnicodeUTF8))
        self.menuHelp.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout.setText(QtGui.QApplication.translate("MainWindow", "About...", None, QtGui.QApplication.UnicodeUTF8))

