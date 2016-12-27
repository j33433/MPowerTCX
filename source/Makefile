all: mainwindow.py about.py

mainwindow.py: mainwindow.ui Makefile
	( cat .disclaimer; pyside-uic mainwindow.ui ) > mainwindow.py

about.py: about.ui Makefile
	( cat .disclaimer; pyside-uic about.ui ) > about.py
	
