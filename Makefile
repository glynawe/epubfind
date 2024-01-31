.PHONY : install uninstall tidy clean

SOURCES=Makefile pyproject.toml setup.py MANIFEST.in \
        LICENCE.txt README.md requirements.txt \
        $(wildcard epubfind/*.py)

install : $(SOURCES)
	python3 -m pip install --prefix ~/.local/ -U -e .

uninstall : $(SOURCES)
	python3 -m pip uninstall -y epubfind-glynawe

tidy:
	rm -rf dist
	rm -rf epubfind/epubfind_glynawe.egg-info
	rm -rf epubfind/epubfind/__pycache__

clean: tidy
	rm -rf dist
