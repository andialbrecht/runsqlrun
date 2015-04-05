icons:
	inkscape -z -f data/icons/runsqlrun.svg -w 128 -e data/icons/128x128/runsqlrun.png

compile-resources:
	glib-compile-resources --target=data/runsqlrun.gresource --sourcedir=data/ data/runsqlrun.gresource.xml
