# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'about.ui',
# licensing of 'about.ui' applies.
#
# Created: Wed Nov 21 18:09:38 2018
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(756, 395)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.labelVersion = QtWidgets.QLabel(Dialog)
        self.labelVersion.setObjectName("labelVersion")
        self.gridLayout.addWidget(self.labelVersion, 0, 0, 1, 1)
        self.labelSupport = QtWidgets.QLabel(Dialog)
        self.labelSupport.setObjectName("labelSupport")
        self.gridLayout.addWidget(self.labelSupport, 1, 0, 1, 1)
        self.labelLicense = QtWidgets.QLabel(Dialog)
        self.labelLicense.setObjectName("labelLicense")
        self.gridLayout.addWidget(self.labelLicense, 2, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/mpowertcx icon flat.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(256, 256))
        self.pushButton.setFlat(True)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 3, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 1, 1, 1)
        self.licenseEdit = QtWidgets.QPlainTextEdit(Dialog)
        self.licenseEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.licenseEdit.setReadOnly(True)
        self.licenseEdit.setObjectName("licenseEdit")
        self.gridLayout.addWidget(self.licenseEdit, 3, 0, 2, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtWidgets.QApplication.translate("Dialog", "MPowerTCX: About", None, -1))
        self.labelVersion.setText(QtWidgets.QApplication.translate("Dialog", "Version:", None, -1))
        self.labelSupport.setText(QtWidgets.QApplication.translate("Dialog", "Support: j33433@gmail.com", None, -1))
        self.labelLicense.setText(QtWidgets.QApplication.translate("Dialog", "License:", None, -1))

#import images_rc
