all: ui/mainwindow.py ui/about.py

ui/mainwindow.py: ui/mainwindow.ui Makefile
	( cat .disclaimer; pyside-uic ui/mainwindow.ui ) > ui/mainwindow.py

ui/about.py: ui/about.ui Makefile
	( cat .disclaimer; pyside-uic ui/about.ui ) > ui/about.py
	
