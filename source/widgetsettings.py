import json

from PySide.QtGui import *
from PySide.QtCore import *

class WidgetSettings(object):
    def __init__(self, parent, filename):
        self.__parent = parent
        self.__filename = filename
    
    def _key_name(self, w):
        return '%s/%s' % (self.__parent.objectName(), w.objectName())
        
    def stash(self):
        print ("stash")
        
        saved = dict()
        lineEdits = self.__parent.findChildren(QAbstractSpinBox)

        for w in lineEdits:
            saved[self._key_name(w)] = w.text()
    
        checkBoxes = self.__parent.findChildren(QCheckBox)
        
        for w in checkBoxes:
            saved[self._key_name(w)] = w.isChecked()

        comboBoxes = self.__parent.findChildren(QComboBox)

        for w in comboBoxes:
            saved[self._key_name(w)] = w.currentText()

        json_data = json.dumps(saved, indent=4, sort_keys=True)
        
        with open(self.__filename, 'w') as json_file:
            json_file.write(json_data + '\n')

    def unstash(self):
        print ("unstash")
        
        try:
            with open(self.__filename, 'r') as json_file:
                saved = json.load(json_file)
        except IOError as e:
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
    
