#
# Load and save most widget states automatically
# 

import json

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class WidgetSettings(object):
    def __init__(self, parent, filename, settings):
        self.__parent = parent
        self.__filename = filename
        self.__settings = settings

    def _key_name(self, w):
        return '%s/%s' % (self.__parent.objectName(), w.objectName())
        
    def stash(self):
        saved = dict()
        lineEdits = self.__parent.findChildren(QAbstractSpinBox)

        for w in lineEdits:
            saved[self._key_name(w)] = str(w.text())
    
        checkBoxes = self.__parent.findChildren(QCheckBox)
        
        for w in checkBoxes:
            saved[self._key_name(w)] = w.isChecked()

        comboBoxes = self.__parent.findChildren(QComboBox)

        for w in comboBoxes:
            saved[self._key_name(w)] = str(w.currentText())

        json_data = json.dumps(saved, indent=4, sort_keys=True)
        self.__settings.setValue("WidgetSettings/json", json_data)

    def unstash(self):
        json_data = self.__settings.value("WidgetSettings/json")

        if json_data != None:
            saved = json.loads(json_data)
        else:
            saved = dict()

        lineEdits = self.__parent.findChildren(QAbstractSpinBox)

        for w in lineEdits:
            if hasattr(w, 'value'):
                v = saved.get(self._key_name(w), w.value())
                w.setValue(w.valueFromText(str(v)))
            else:
                # Probably a date time thing
                print ("can't stash %r" % w)
                
        checkBoxes = self.__parent.findChildren(QCheckBox)
        
        for w in checkBoxes:
            v = saved.get(self._key_name(w), w.isChecked())
            w.setCheckState(Qt.Checked if v else Qt.Unchecked)

        comboBoxes = self.__parent.findChildren(QComboBox)

        for w in comboBoxes:
            v = saved.get(self._key_name(w), w.currentText())
            index = w.findText(v, Qt.MatchFixedString)
            
            if index >= 0:
                w.setCurrentIndex(index)
    
