all: icons compile-resources

data/icons/128x128:
	mkdir -p data/icons/128x128

icons: data/icons/128x128
	inkscape -z -f data/icons/runsqlrun.svg -w 128 -e data/icons/128x128/runsqlrun.png

compile-resources:
	glib-compile-resources --target=data/runsqlrun.gresource --sourcedir=data/ data/runsqlrun.gresource.xml

bootstrap-debian: install-deps-debian all

install-deps-debian:
	@sudo apt-get install python3 python3-gi python3-keyring python3-sqlparse python3-xdg python3-cairo inkscape libglib2.0-bin python3-psycopg2
