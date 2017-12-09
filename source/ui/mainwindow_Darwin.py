#
# MPowerTCX: Share Schwinn A.C. indoor cycle data with Strava, GoldenCheetah 
# and other apps.
#
# Copyright (C) 2016-2017 James Roth
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

# Form implementation generated from reading ui file 'ui/mainwindow.ui'
#
# Created: Sat Dec  9 16:19:54 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(680, 458)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_3 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_3.setContentsMargins(12, 12, 12, 12)
        self.gridLayout_3.setHorizontalSpacing(16)
        self.gridLayout_3.setVerticalSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox = QtGui.QGroupBox(self.centralwidget)
        self.groupBox.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setContentsMargins(16, 16, 16, 16)
        self.gridLayout.setHorizontalSpacing(12)
        self.gridLayout.setVerticalSpacing(8)
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
        self.useFileDate = QtGui.QCheckBox(self.groupBox)
        self.useFileDate.setObjectName("useFileDate")
        self.gridLayout.addWidget(self.useFileDate, 1, 0, 1, 2)
        self.checkBoxExtra = QtGui.QCheckBox(self.groupBox)
        self.checkBoxExtra.setObjectName("checkBoxExtra")
        self.gridLayout.addWidget(self.checkBoxExtra, 3, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_2 = QtGui.QGroupBox(self.centralwidget)
        self.groupBox_2.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setContentsMargins(16, 16, 16, 16)
        self.gridLayout_2.setHorizontalSpacing(12)
        self.gridLayout_2.setVerticalSpacing(8)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.labelDurationName = QtGui.QLabel(self.groupBox_2)
        self.labelDurationName.setObjectName("labelDurationName")
        self.gridLayout_2.addWidget(self.labelDurationName, 1, 0, 1, 1)
        self.labelDuration = QtGui.QLabel(self.groupBox_2)
        self.labelDuration.setText("")
        self.labelDuration.setObjectName("labelDuration")
        self.gridLayout_2.addWidget(self.labelDuration, 1, 1, 1, 1)
        self.labelAveragePowerName = QtGui.QLabel(self.groupBox_2)
        self.labelAveragePowerName.setObjectName("labelAveragePowerName")
        self.gridLayout_2.addWidget(self.labelAveragePowerName, 2, 0, 1, 1)
        self.labelAveragePower = QtGui.QLabel(self.groupBox_2)
        self.labelAveragePower.setText("")
        self.labelAveragePower.setObjectName("labelAveragePower")
        self.gridLayout_2.addWidget(self.labelAveragePower, 2, 1, 1, 1)
        self.labelMaxPowerName = QtGui.QLabel(self.groupBox_2)
        self.labelMaxPowerName.setObjectName("labelMaxPowerName")
        self.gridLayout_2.addWidget(self.labelMaxPowerName, 3, 0, 1, 1)
        self.labelMaxPower = QtGui.QLabel(self.groupBox_2)
        self.labelMaxPower.setText("")
        self.labelMaxPower.setObjectName("labelMaxPower")
        self.gridLayout_2.addWidget(self.labelMaxPower, 3, 1, 1, 1)
        self.labelEquipmentName = QtGui.QLabel(self.groupBox_2)
        self.labelEquipmentName.setObjectName("labelEquipmentName")
        self.gridLayout_2.addWidget(self.labelEquipmentName, 0, 0, 1, 1)
        self.labelEquipment = QtGui.QLabel(self.groupBox_2)
        self.labelEquipment.setText("")
        self.labelEquipment.setObjectName("labelEquipment")
        self.gridLayout_2.addWidget(self.labelEquipment, 0, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem1, 4, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 1, 1, 1)
        self.groupBoxPhysics = QtGui.QGroupBox(self.centralwidget)
        self.groupBoxPhysics.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBoxPhysics.setFlat(True)
        self.groupBoxPhysics.setObjectName("groupBoxPhysics")
        self.gridLayout_5 = QtGui.QGridLayout(self.groupBoxPhysics)
        self.gridLayout_5.setContentsMargins(16, 16, 16, 16)
        self.gridLayout_5.setHorizontalSpacing(12)
        self.gridLayout_5.setVerticalSpacing(8)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.label = QtGui.QLabel(self.groupBoxPhysics)
        self.label.setObjectName("label")
        self.gridLayout_5.addWidget(self.label, 1, 0, 1, 1)
        self.doubleSpinBoxRiderWeight = QtGui.QDoubleSpinBox(self.groupBoxPhysics)
        self.doubleSpinBoxRiderWeight.setDecimals(1)
        self.doubleSpinBoxRiderWeight.setMaximum(1000.0)
        self.doubleSpinBoxRiderWeight.setProperty("value", 70.0)
        self.doubleSpinBoxRiderWeight.setObjectName("doubleSpinBoxRiderWeight")
        self.gridLayout_5.addWidget(self.doubleSpinBoxRiderWeight, 1, 1, 1, 1)
        self.comboBoxUnits = QtGui.QComboBox(self.groupBoxPhysics)
        self.comboBoxUnits.setObjectName("comboBoxUnits")
        self.comboBoxUnits.addItem("")
        self.comboBoxUnits.addItem("")
        self.gridLayout_5.addWidget(self.comboBoxUnits, 1, 2, 1, 1)
        self.label_2 = QtGui.QLabel(self.groupBoxPhysics)
        self.label_2.setObjectName("label_2")
        self.gridLayout_5.addWidget(self.label_2, 2, 0, 1, 1)
        self.doubleSpinBoxBikeWeight = QtGui.QDoubleSpinBox(self.groupBoxPhysics)
        self.doubleSpinBoxBikeWeight.setDecimals(1)
        self.doubleSpinBoxBikeWeight.setMaximum(1000.0)
        self.doubleSpinBoxBikeWeight.setProperty("value", 8.0)
        self.doubleSpinBoxBikeWeight.setObjectName("doubleSpinBoxBikeWeight")
        self.gridLayout_5.addWidget(self.doubleSpinBoxBikeWeight, 2, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem2, 3, 0, 1, 1)
        self.checkBoxPhysics = QtGui.QCheckBox(self.groupBoxPhysics)
        self.checkBoxPhysics.setObjectName("checkBoxPhysics")
        self.gridLayout_5.addWidget(self.checkBoxPhysics, 0, 0, 1, 3)
        self.gridLayout_3.addWidget(self.groupBoxPhysics, 1, 0, 1, 1)
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setObjectName("widget")
        self.gridLayout_4 = QtGui.QGridLayout(self.widget)
        self.gridLayout_4.setContentsMargins(16, 20, 16, 16)
        self.gridLayout_4.setHorizontalSpacing(16)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.saveButton = QtGui.QPushButton(self.widget)
        self.saveButton.setMinimumSize(QtCore.QSize(0, 32))
        self.saveButton.setStyleSheet("")
        self.saveButton.setObjectName("saveButton")
        self.gridLayout_4.addWidget(self.saveButton, 1, 1, 1, 1)
        self.loadButton = QtGui.QPushButton(self.widget)
        self.loadButton.setMinimumSize(QtCore.QSize(0, 32))
        self.loadButton.setStyleSheet("")
        self.loadButton.setObjectName("loadButton")
        self.gridLayout_4.addWidget(self.loadButton, 1, 0, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem3, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.widget, 2, 0, 1, 2)
        self.groupBoxCompatibility = QtGui.QGroupBox(self.centralwidget)
        self.groupBoxCompatibility.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBoxCompatibility.setFlat(True)
        self.groupBoxCompatibility.setObjectName("groupBoxCompatibility")
        self.gridLayout_6 = QtGui.QGridLayout(self.groupBoxCompatibility)
        self.gridLayout_6.setContentsMargins(16, 16, 16, 16)
        self.gridLayout_6.setHorizontalSpacing(12)
        self.gridLayout_6.setVerticalSpacing(8)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.checkBoxInterpolate = QtGui.QCheckBox(self.groupBoxCompatibility)
        self.checkBoxInterpolate.setChecked(True)
        self.checkBoxInterpolate.setObjectName("checkBoxInterpolate")
        self.gridLayout_6.addWidget(self.checkBoxInterpolate, 0, 0, 1, 1)
        spacerItem4 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_6.addItem(spacerItem4, 1, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBoxCompatibility, 1, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 680, 20))
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
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.labelWorkoutTime.setText(QtGui.QApplication.translate("MainWindow", "Workout Time:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelPowerAdjustment.setText(QtGui.QApplication.translate("MainWindow", "Power Adjustment:", None, QtGui.QApplication.UnicodeUTF8))
        self.powerAdjustment.setSuffix(QtGui.QApplication.translate("MainWindow", "%", None, QtGui.QApplication.UnicodeUTF8))
        self.useFileDate.setText(QtGui.QApplication.translate("MainWindow", "Use File Time as Workout Time", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBoxExtra.setText(QtGui.QApplication.translate("MainWindow", "Show Extra Options", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("MainWindow", "Workout Info", None, QtGui.QApplication.UnicodeUTF8))
        self.labelDurationName.setText(QtGui.QApplication.translate("MainWindow", "Duration:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelAveragePowerName.setText(QtGui.QApplication.translate("MainWindow", "Average Power:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelMaxPowerName.setText(QtGui.QApplication.translate("MainWindow", "Max Power:", None, QtGui.QApplication.UnicodeUTF8))
        self.labelEquipmentName.setText(QtGui.QApplication.translate("MainWindow", "Equipment:", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBoxPhysics.setTitle(QtGui.QApplication.translate("MainWindow", "Physics", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Rider Weight:", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBoxUnits.setItemText(0, QtGui.QApplication.translate("MainWindow", "kg", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBoxUnits.setItemText(1, QtGui.QApplication.translate("MainWindow", "lbs", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Bike Weight:", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBoxPhysics.setText(QtGui.QApplication.translate("MainWindow", "Recalcuate Speed and Distance", None, QtGui.QApplication.UnicodeUTF8))
        self.saveButton.setText(QtGui.QApplication.translate("MainWindow", "Save TCX...", None, QtGui.QApplication.UnicodeUTF8))
        self.loadButton.setText(QtGui.QApplication.translate("MainWindow", "Load CSV...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBoxCompatibility.setTitle(QtGui.QApplication.translate("MainWindow", "Compatibility", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBoxInterpolate.setText(QtGui.QApplication.translate("MainWindow", "Interpolate", None, QtGui.QApplication.UnicodeUTF8))
        self.menuHelp.setTitle(QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAbout.setText(QtGui.QApplication.translate("MainWindow", "About...", None, QtGui.QApplication.UnicodeUTF8))

import images_rc