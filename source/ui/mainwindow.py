# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui',
# licensing of 'mainwindow.ui' applies.
#
# Created: Wed Nov 21 18:09:29 2018
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(680, 458)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_3.setContentsMargins(12, 12, 12, 12)
        self.gridLayout_3.setHorizontalSpacing(16)
        self.gridLayout_3.setVerticalSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBox.setFlat(True)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setContentsMargins(16, 16, 16, 16)
        self.gridLayout.setHorizontalSpacing(12)
        self.gridLayout.setVerticalSpacing(8)
        self.gridLayout.setObjectName("gridLayout")
        self.labelWorkoutTime = QtWidgets.QLabel(self.groupBox)
        self.labelWorkoutTime.setObjectName("labelWorkoutTime")
        self.gridLayout.addWidget(self.labelWorkoutTime, 0, 0, 1, 1)
        self.workoutTime = QtWidgets.QDateTimeEdit(self.groupBox)
        self.workoutTime.setObjectName("workoutTime")
        self.gridLayout.addWidget(self.workoutTime, 0, 1, 1, 1)
        self.labelPowerAdjustment = QtWidgets.QLabel(self.groupBox)
        self.labelPowerAdjustment.setObjectName("labelPowerAdjustment")
        self.gridLayout.addWidget(self.labelPowerAdjustment, 2, 0, 1, 1)
        self.powerAdjustment = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.powerAdjustment.setMinimum(-100.0)
        self.powerAdjustment.setMaximum(100.0)
        self.powerAdjustment.setSingleStep(0.1)
        self.powerAdjustment.setObjectName("powerAdjustment")
        self.gridLayout.addWidget(self.powerAdjustment, 2, 1, 1, 1)
        self.useFileDate = QtWidgets.QCheckBox(self.groupBox)
        self.useFileDate.setObjectName("useFileDate")
        self.gridLayout.addWidget(self.useFileDate, 1, 0, 1, 2)
        self.checkBoxExtra = QtWidgets.QCheckBox(self.groupBox)
        self.checkBoxExtra.setObjectName("checkBoxExtra")
        self.gridLayout.addWidget(self.checkBoxExtra, 3, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setContentsMargins(16, 16, 16, 16)
        self.gridLayout_2.setHorizontalSpacing(12)
        self.gridLayout_2.setVerticalSpacing(8)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.labelDurationName = QtWidgets.QLabel(self.groupBox_2)
        self.labelDurationName.setObjectName("labelDurationName")
        self.gridLayout_2.addWidget(self.labelDurationName, 1, 0, 1, 1)
        self.labelDuration = QtWidgets.QLabel(self.groupBox_2)
        self.labelDuration.setText("")
        self.labelDuration.setObjectName("labelDuration")
        self.gridLayout_2.addWidget(self.labelDuration, 1, 1, 1, 1)
        self.labelAveragePowerName = QtWidgets.QLabel(self.groupBox_2)
        self.labelAveragePowerName.setObjectName("labelAveragePowerName")
        self.gridLayout_2.addWidget(self.labelAveragePowerName, 2, 0, 1, 1)
        self.labelAveragePower = QtWidgets.QLabel(self.groupBox_2)
        self.labelAveragePower.setText("")
        self.labelAveragePower.setObjectName("labelAveragePower")
        self.gridLayout_2.addWidget(self.labelAveragePower, 2, 1, 1, 1)
        self.labelMaxPowerName = QtWidgets.QLabel(self.groupBox_2)
        self.labelMaxPowerName.setObjectName("labelMaxPowerName")
        self.gridLayout_2.addWidget(self.labelMaxPowerName, 3, 0, 1, 1)
        self.labelMaxPower = QtWidgets.QLabel(self.groupBox_2)
        self.labelMaxPower.setText("")
        self.labelMaxPower.setObjectName("labelMaxPower")
        self.gridLayout_2.addWidget(self.labelMaxPower, 3, 1, 1, 1)
        self.labelEquipmentName = QtWidgets.QLabel(self.groupBox_2)
        self.labelEquipmentName.setObjectName("labelEquipmentName")
        self.gridLayout_2.addWidget(self.labelEquipmentName, 0, 0, 1, 1)
        self.labelEquipment = QtWidgets.QLabel(self.groupBox_2)
        self.labelEquipment.setText("")
        self.labelEquipment.setObjectName("labelEquipment")
        self.gridLayout_2.addWidget(self.labelEquipment, 0, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem1, 4, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 1, 1, 1)
        self.groupBoxPhysics = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBoxPhysics.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBoxPhysics.setFlat(True)
        self.groupBoxPhysics.setObjectName("groupBoxPhysics")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBoxPhysics)
        self.gridLayout_5.setContentsMargins(16, 16, 16, 16)
        self.gridLayout_5.setHorizontalSpacing(12)
        self.gridLayout_5.setVerticalSpacing(8)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.label = QtWidgets.QLabel(self.groupBoxPhysics)
        self.label.setObjectName("label")
        self.gridLayout_5.addWidget(self.label, 1, 0, 1, 1)
        self.doubleSpinBoxRiderWeight = QtWidgets.QDoubleSpinBox(self.groupBoxPhysics)
        self.doubleSpinBoxRiderWeight.setDecimals(1)
        self.doubleSpinBoxRiderWeight.setMaximum(1000.0)
        self.doubleSpinBoxRiderWeight.setProperty("value", 70.0)
        self.doubleSpinBoxRiderWeight.setObjectName("doubleSpinBoxRiderWeight")
        self.gridLayout_5.addWidget(self.doubleSpinBoxRiderWeight, 1, 1, 1, 1)
        self.comboBoxUnits = QtWidgets.QComboBox(self.groupBoxPhysics)
        self.comboBoxUnits.setObjectName("comboBoxUnits")
        self.comboBoxUnits.addItem("")
        self.comboBoxUnits.addItem("")
        self.gridLayout_5.addWidget(self.comboBoxUnits, 1, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBoxPhysics)
        self.label_2.setObjectName("label_2")
        self.gridLayout_5.addWidget(self.label_2, 2, 0, 1, 1)
        self.doubleSpinBoxBikeWeight = QtWidgets.QDoubleSpinBox(self.groupBoxPhysics)
        self.doubleSpinBoxBikeWeight.setDecimals(1)
        self.doubleSpinBoxBikeWeight.setMaximum(1000.0)
        self.doubleSpinBoxBikeWeight.setProperty("value", 8.0)
        self.doubleSpinBoxBikeWeight.setObjectName("doubleSpinBoxBikeWeight")
        self.gridLayout_5.addWidget(self.doubleSpinBoxBikeWeight, 2, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem2, 3, 0, 1, 1)
        self.checkBoxPhysics = QtWidgets.QCheckBox(self.groupBoxPhysics)
        self.checkBoxPhysics.setObjectName("checkBoxPhysics")
        self.gridLayout_5.addWidget(self.checkBoxPhysics, 0, 0, 1, 3)
        self.gridLayout_3.addWidget(self.groupBoxPhysics, 1, 0, 1, 1)
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setObjectName("widget")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_4.setContentsMargins(16, 20, 16, 16)
        self.gridLayout_4.setHorizontalSpacing(16)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.saveButton = QtWidgets.QPushButton(self.widget)
        self.saveButton.setMinimumSize(QtCore.QSize(0, 32))
        self.saveButton.setStyleSheet("")
        self.saveButton.setObjectName("saveButton")
        self.gridLayout_4.addWidget(self.saveButton, 1, 1, 1, 1)
        self.loadButton = QtWidgets.QPushButton(self.widget)
        self.loadButton.setMinimumSize(QtCore.QSize(0, 32))
        self.loadButton.setStyleSheet("")
        self.loadButton.setObjectName("loadButton")
        self.gridLayout_4.addWidget(self.loadButton, 1, 0, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem3, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.widget, 2, 0, 1, 2)
        self.groupBoxCompatibility = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBoxCompatibility.setMinimumSize(QtCore.QSize(320, 160))
        self.groupBoxCompatibility.setFlat(True)
        self.groupBoxCompatibility.setObjectName("groupBoxCompatibility")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.groupBoxCompatibility)
        self.gridLayout_6.setContentsMargins(16, 16, 16, 16)
        self.gridLayout_6.setHorizontalSpacing(12)
        self.gridLayout_6.setVerticalSpacing(8)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.checkBoxInterpolate = QtWidgets.QCheckBox(self.groupBoxCompatibility)
        self.checkBoxInterpolate.setChecked(True)
        self.checkBoxInterpolate.setObjectName("checkBoxInterpolate")
        self.gridLayout_6.addWidget(self.checkBoxInterpolate, 0, 0, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_6.addItem(spacerItem4, 1, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBoxCompatibility, 1, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 680, 20))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionAbout = QtWidgets.QAction(MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.menuHelp.addAction(self.actionAbout)
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MPowerTCX", None, -1))
        self.groupBox.setTitle(QtWidgets.QApplication.translate("MainWindow", "Options", None, -1))
        self.labelWorkoutTime.setText(QtWidgets.QApplication.translate("MainWindow", "Workout Time:", None, -1))
        self.labelPowerAdjustment.setText(QtWidgets.QApplication.translate("MainWindow", "Power Adjustment:", None, -1))
        self.powerAdjustment.setSuffix(QtWidgets.QApplication.translate("MainWindow", "%", None, -1))
        self.useFileDate.setText(QtWidgets.QApplication.translate("MainWindow", "Use File Time as Workout Time", None, -1))
        self.checkBoxExtra.setText(QtWidgets.QApplication.translate("MainWindow", "Show Extra Options", None, -1))
        self.groupBox_2.setTitle(QtWidgets.QApplication.translate("MainWindow", "Workout Info", None, -1))
        self.labelDurationName.setText(QtWidgets.QApplication.translate("MainWindow", "Duration:", None, -1))
        self.labelAveragePowerName.setText(QtWidgets.QApplication.translate("MainWindow", "Average Power:", None, -1))
        self.labelMaxPowerName.setText(QtWidgets.QApplication.translate("MainWindow", "Max Power:", None, -1))
        self.labelEquipmentName.setText(QtWidgets.QApplication.translate("MainWindow", "Equipment:", None, -1))
        self.groupBoxPhysics.setTitle(QtWidgets.QApplication.translate("MainWindow", "Physics", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "Rider Weight:", None, -1))
        self.comboBoxUnits.setItemText(0, QtWidgets.QApplication.translate("MainWindow", "kg", None, -1))
        self.comboBoxUnits.setItemText(1, QtWidgets.QApplication.translate("MainWindow", "lbs", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("MainWindow", "Bike Weight:", None, -1))
        self.checkBoxPhysics.setText(QtWidgets.QApplication.translate("MainWindow", "Recalculate Speed and Distance", None, -1))
        self.saveButton.setText(QtWidgets.QApplication.translate("MainWindow", "Save TCX...", None, -1))
        self.loadButton.setText(QtWidgets.QApplication.translate("MainWindow", "Load CSV...", None, -1))
        self.groupBoxCompatibility.setTitle(QtWidgets.QApplication.translate("MainWindow", "Compatibility", None, -1))
        self.checkBoxInterpolate.setText(QtWidgets.QApplication.translate("MainWindow", "Interpolate", None, -1))
        self.menuHelp.setTitle(QtWidgets.QApplication.translate("MainWindow", "Help", None, -1))
        self.actionAbout.setText(QtWidgets.QApplication.translate("MainWindow", "About...", None, -1))

#import images_rc
