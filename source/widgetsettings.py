import json

from PySide.QtGui import *
from PySide.QtCore import *

class WidgetSettings(object):
    def __init__(self, parent, filename):
        self.__parent = parent
        self.__filename = filename
    
    def stash(self):
        print ("stash")
        
        saved = dict()
        lineEdits = self.__parent.findChildren(QAbstractSpinBox)

        for w in lineEdits:
            #print ("%s %r" % (w.objectName(), w.text()))
            saved[w.objectName()] = w.text()
    
        checkBoxes = self.__parent.findChildren(QCheckBox)
        
        for w in checkBoxes:
            #print ("%s %r" % (w.objectName(), w.checkState()))
            saved[w.objectName()] = w.isChecked()

        comboBoxes = self.__parent.findChildren(QComboBox)

        for w in comboBoxes:
            #print ("%s %r" % (w.objectName(), w.currentText()))
            saved[w.objectName()] = w.currentText()

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
                v = saved.get(w.objectName(), w.value())
                w.setValue(w.valueFromText(str(v)))
            else:
                # Probably a date time thing
                print ("can't stash %r" % w)
                
        checkBoxes = self.__parent.findChildren(QCheckBox)
        
        for w in checkBoxes:
            v = saved.get(w.objectName(), w.isChecked())
            #print ("%s %r" % (w.objectName(), v))
            w.setCheckState(Qt.Checked if v else Qt.Unchecked)

        comboBoxes = self.__parent.findChildren(QComboBox)

        for w in comboBoxes:
            v = saved.get(w.objectName(), w.currentText())
            #print ("%s %r" % (w.objectName(), v))
            index = w.findText(v, Qt.MatchFixedString)
            
            if index >= 0:
                w.setCurrentIndex(index)
    
