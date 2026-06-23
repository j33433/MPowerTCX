OS=$(shell uname -s)

ifeq ($(OS),Darwin)
    PLATFORM=_Darwin
else
    PLATFROM=
endif

UIC=pyside2-uic

all: ui/mainwindow$(PLATFROM).py ui/about$(PLATFORM).py ui/images_rc.py

#ui/images_rc.py: ui/images.qrc Makefile
#	pyside-rcc -o ui/images_rc.py ui/images.qrc
	
ui/mainwindow$(PLATFORM).py: ui/mainwindow.ui Makefile
	( cat .disclaimer; $(UIC) ui/mainwindow.ui ) > ui/mainwindow.py.tmp
	mv ui/mainwindow.py.tmp ui/mainwindow$(PLATFORM).py

ui/about$(PLATFORM).py: ui/about.ui Makefile
	( cat .disclaimer; $(UIC) ui/about.ui ) > ui/about.py.tmp
	mv ui/about.py.tmp ui/about$(PLATFORM).py
	
