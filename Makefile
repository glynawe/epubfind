.PHONY : install uninstall tidy clean

SOURCES=Makefile pyproject.toml setup.py MANIFEST.in \
        LICENCE.txt README.md requirements.txt \
        $(wildcard epubsearch/*.py)

install : $(SOURCES)
	python3 -m pip install --prefix ~/.local/ -U -e .

uninstall : $(SOURCES)
	python3 -m pip uninstall -y epubsearch-glynawe

tidy:
	rm -rf dist
	rm -rf epubsearch/epubsearch_glynawe.egg-info
	rm -rf epubsearch/epubsearch/__pycache__

clean: tidy
	rm -rf dist
