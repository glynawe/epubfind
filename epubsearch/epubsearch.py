#!/usr/bin/env python3

"""This script searches for a string within all the EPUB ebooks in a directory tree.
The titles and file names of the EPUBs that match and their matching paragraphs will 
be output. The search string is case-insensitive and ignores the width of spacing 
between words. The search string can be a regexp.
"""

# EPUBs are actually ZIP files containing directories of XHTML text files.
# This script opens those XHTML files, uses lxml to extract heading and paragraph
# text then searches that text with a regex derived from the search string.


from typing import TextIO, Iterator, List, Tuple, Pattern
from os import walk
from re import compile, sub, IGNORECASE
from io import TextIOWrapper
from sys import stderr, exit
from zipfile import ZipFile
from pathlib import Path
from textwrap import wrap
from argparse import ArgumentParser
from importlib.util import find_spec

if not find_spec('lxml'):  # In case this script is used stand-alone.
    print(__doc__, file=stderr)
    print("*** THIS SCRIPT REQUIRES THE LXML LIBRARY: run 'pip3 install lxml'", file=stderr)
    exit(1)

from lxml import html, etree


XMLNS = {   # The XML namespaces used in EPUB XML files.
    'dc': "http://purl.org/dc/elements/1.1/",
    'dcterms': "http://purl.org/dc/terms/",
    'opf': "http://www.idpf.org/2007/opf",
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}


# Special EPUB XHTML parser: EPUB files are always encoded in UTF-8
# unless they say otherwise; parse XHTML with lxml's more forgiving 
# HTML parser to allow some slack for badly made EPUBs.

epub_xhtml_parser = html.HTMLParser(encoding='utf-8')


def get_opf(epub: ZipFile) -> str:
    """ Find the OPF file that contains the ebook's basic metadata."""
    with epub.open('META-INF/container.xml', 'r') as file:
        xml = etree.parse(file)
        return xml.xpath('//container:rootfile/@full-path', namespaces=XMLNS)[0]


def get_title(epub_path: Path) -> str:
    """Get the ebook's title from its metadata file."""
    with ZipFile(epub_path, 'r') as epub:
        with epub.open(get_opf(epub), 'r') as file:
            xml = etree.parse(file)
            return xml.xpath('//dc:title', namespaces=XMLNS)[0].text.strip()


def files(path: Path, extension: str = '') -> Iterator[Path]:
    """Iterate through the files in a directory path.
       (But if the path argument is a file then only yield that.)"""
    if path.is_file() and path.name.endswith(extension):
        yield path
    elif path.is_dir():
        for dir_path, _, filenames in walk(path):
            for filename in filenames:
                if filename.endswith(extension):
                    yield Path(dir_path, filename)
    else:
        raise FileNotFoundError()


def open_zipped_files(zipfile: Path, extension: str = '') -> Iterator[TextIO]:
    """Open each file in a Zip file for reading in Unicode text mode."""
    with ZipFile(zipfile, mode='r') as unzipper:
        for name in unzipper.namelist():
            if name.endswith(extension):
                with unzipper.open(name, mode='r') as file_handle:
                    yield TextIOWrapper(file_handle, encoding='utf-8')


def search_pattern(search_string: str) -> Pattern[str]:
    """Compile the regex from the search string provided on the command line.
       (See the documentation at the top of this file.)"""
    s = search_string.strip()
    s = sub(r'\s+', r'\\s+', s)  # spaces match any number of spaces
    s = r'\b' + s + r'\b'  # only full words get matched
    return compile(s, IGNORECASE)


# The type for search results:
Heading = str
Paragraph = str
Title = str
Chapter = Tuple[Heading, List[Paragraph]]  # chapter heading, matching paragraphs
SearchResult = Tuple[Path, Title, List[Chapter]]  # path to book, book title, chapter results


def search(path: Path, search_string: str) -> Iterator[SearchResult]:
    """Main function: search all the EPUBs in a directory tree for the search string."""
    pattern = search_pattern(search_string)
    for epub_path in files(path, extension='.epub'):
        chapters: List[Chapter] = []
        paragraphs: List[Paragraph] = []
        heading = ''
        for file in open_zipped_files(epub_path, extension='.xhtml'):
            xhtml = html.parse(file, parser=epub_xhtml_parser)
            for element in xhtml.xpath('//p|//h1|//h2|//h3'):
                text = element.text_content()
                if element.tag != 'p':  # is a heading
                    if paragraphs:
                        chapters.append((heading, paragraphs))
                        paragraphs = []
                    heading = text
                if pattern.search(text):
                    paragraphs.append('\n'.join(wrap(text)))
        if paragraphs:
            chapters.append((heading, paragraphs))
        if chapters:
            yield epub_path, get_title(epub_path), chapters


def show(result: SearchResult, bare: bool) -> None:
    """ Display the search result for one EPUB in the terminal.""" 
    epub, title, chapters = result
    if bare:
        print(str(epub))
    else:
        print()
        print('-' * 70)
        print(title)
        print()
        print(str(epub))
        print('-' * 70)
        for heading, paragraphs in chapters:
            if heading:
                print()
                print('- ' * 35)
                print(heading)
                print('- ' * 35)
            for s in paragraphs:
                print()
                print(s)


def main():
    parser = ArgumentParser(description=__doc__)  # the doc string at the top of this file
    parser.add_argument('-b', '--bare', action='store_true', help='just output filenames')
    parser.add_argument('epub', type=Path, help='an epub file or a directory containing EPUB files')
    parser.add_argument('string', type=str, help='the search string')
    args = parser.parse_args()

    try:
        for result in search(args.epub, args.string):
            show(result, args.bare)
    except FileNotFoundError:
        print(f'Not found: {repr(str(args.epub))}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main()

# end
