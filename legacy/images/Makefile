ICO=mpowertcx\ icon\ flat.ico
SVG=mpowertcx\ icon\ flat.svg
PNG=../source/ui/mpowertcx\ icon\ flat.png

all: $(ICO) $(PNG)

$(ICO) $(PNG): $(SVG)
	mkdir -p tmp
	./svg2ico.py $(SVG)
	cp tmp/256.png $(PNG)
	
	
	