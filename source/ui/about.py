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

# Form implementation generated from reading ui file 'ui/about.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(756, 395)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.labelVersion = QtGui.QLabel(Dialog)
        self.labelVersion.setObjectName(_fromUtf8("labelVersion"))
        self.gridLayout.addWidget(self.labelVersion, 0, 0, 1, 1)
        self.labelSupport = QtGui.QLabel(Dialog)
        self.labelSupport.setObjectName(_fromUtf8("labelSupport"))
        self.gridLayout.addWidget(self.labelSupport, 1, 0, 1, 1)
        self.labelLicense = QtGui.QLabel(Dialog)
        self.labelLicense.setObjectName(_fromUtf8("labelLicense"))
        self.gridLayout.addWidget(self.labelLicense, 2, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/mpowertcx icon flat.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(256, 256))
        self.pushButton.setFlat(True)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 3, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 1, 1, 1)
        self.licenseEdit = QtGui.QPlainTextEdit(Dialog)
        self.licenseEdit.setFrameShape(QtGui.QFrame.NoFrame)
        self.licenseEdit.setReadOnly(True)
        self.licenseEdit.setObjectName(_fromUtf8("licenseEdit"))
        self.gridLayout.addWidget(self.licenseEdit, 3, 0, 2, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "MPowerTCX: About", None))
        self.labelVersion.setText(_translate("Dialog", "Version:", None))
        self.labelSupport.setText(_translate("Dialog", "Support: j33433@gmail.com", None))
        self.labelLicense.setText(_translate("Dialog", "License:", None))

from . import images_rc
