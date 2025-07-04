#!/usr/bin/env python3

"""Epubfind searches for sets of phrases within an EPUB ebook, 
or within all every ebook in a directory. 

A paragraph from an ebook matches if it contains all the search 
phrases. Those matching paragraphs will be output. Groups of 
matching paragraphs will be given book title and chapter headings 
so that they can be located in the book.

Search phrases are case-insensitive. A phrase can be a single word
or a string of several words in quotes. E.g. 'suddenly vanish away'.
The width of the spacing between words is ignored. 

A phrase may also be a regular expression pattern. This is good when 
looking for alternatives. The pattern 'beamish|uffish' will find 
paragraphs containing either "beamish" or "uffish"."""

# EPUBs are basically ZIP files containing directories of HTML text files.
# This script opens those files, uses lxml to extract heading and paragraph
# text and searches that text with a regex derived from a search phrase.


from typing import TextIO, Iterator, List, Tuple, Pattern
from os import walk
from re import compile, sub, IGNORECASE
from io import TextIOWrapper
from sys import stderr, exit
from zipfile import ZipFile
from pathlib import Path
from textwrap import wrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from importlib.util import find_spec

if not find_spec('lxml'):  # In case this script is used stand-alone.
    print(__doc__, file=stderr)
    print("*** EPUBFIND REQUIRES THE LXML LIBRARY: run 'pip3 install lxml'", file=stderr)
    exit(1)

from lxml import html, etree

XMLNS = {   # The XML namespaces used in EPUB XML files.
    'dc': "http://purl.org/dc/elements/1.1/",
    'dcterms': "http://purl.org/dc/terms/",
    'opf': "http://www.idpf.org/2007/opf",
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}


# EPUB HTML files are always encoded in UTF-8 unless they say otherwise.

epub_html_parser = html.HTMLParser(encoding='utf-8')


def get_opf(epub: ZipFile) -> str:
    """ Find the OPF file that contains the ebook's basic metadata."""
    with epub.open('META-INF/container.xml', 'r') as file:
        xml = etree.parse(file, etree.XMLParser)
        return xml.xpath('//container:rootfile/@full-path', namespaces=XMLNS)[0]


def get_title(epub_path: Path) -> str:
    """Get the ebook's title from its metadata file."""
    with ZipFile(epub_path, 'r') as epub:
        with epub.open(get_opf(epub), 'r') as file:
            xml = etree.parse(file, etree.XMLParser)
            try:
                return xml.xpath('//dc:title', namespaces=XMLNS)[0].text.strip()
            except IndexError:
                return ''


def has_extension(name: str, extensions: List[str]) -> bool:
    return not extensions or any(name.endswith(e) for e in extensions)


def files(path: Path, extensions: List[str] = []) -> Iterator[Path]:
    """Iterate through files in a directory path.
       (But if the path argument is a file then only yield that.)"""
    if path.is_file() and has_extension(path.name, extensions):
        yield path
    elif path.is_dir():
        for dir_path, _, filenames in walk(path):
            for filename in filenames:
                if has_extension(filename, extensions):
                    yield Path(dir_path, filename)
    else:
        raise FileNotFoundError()


def open_zipped_files(zipfile: Path, extensions: List[str] = []) -> Iterator[TextIO]:
    """Open each file in a Zip file for reading in Unicode text mode."""
    with ZipFile(zipfile, mode='r') as unzipper:
        for name in unzipper.namelist():
            if has_extension(name, extensions):
                with unzipper.open(name, mode='r') as file_handle:
                    yield TextIOWrapper(file_handle, encoding='utf-8')


def search_pattern(search_phrase: str) -> Pattern[str]:
    """Compile the regex from the search phrase provided on the command line.
       (See the documentation at the top of this file.)"""
    s = search_phrase.strip()
    s = sub(r'\s+', r'\\s+', s)  # spaces match any number of spaces
    s = r'\b' + s + r'\b'  # only full words get matched
    return compile(s, IGNORECASE)


# The type for search results:
Heading = str
Paragraph = str
Title = str
Chapter = Tuple[Heading, List[Paragraph]]  # chapter heading, matching paragraphs
SearchResult = Tuple[Path, Title, List[Chapter]]  # path to book, book title, chapter results


def search(path: Path, search_phrases: list[str], no_wrap: bool) -> Iterator[SearchResult]:
    """Main function: search all the EPUBs in a directory tree for the search phrase."""
    patterns = list(map(search_pattern, search_phrases))
    errors = []
    for epub_path in files(path, extensions=['.epub']):
        chapters: List[Chapter] = []
        paragraphs: List[Paragraph] = []
        heading = ''
        try:
            for file in open_zipped_files(epub_path, extensions=['.html', '.xhtml', '.htm']):
                xhtml = html.parse(file, parser=epub_html_parser)
                for element in xhtml.xpath('//p|//h1|//h2|//h3'):
                    text = element.text_content()
                    if element.tag != 'p':  # is a heading
                        if paragraphs:
                            chapters.append((heading, paragraphs))
                            paragraphs = []
                        heading = text
                    elif all(p.search(text) for p in patterns):
                        paragraphs.append('\n'.join([text] if no_wrap else wrap(text)))
        except Exception as e:
            errors.append(f'error in {epub_path}: {str(e)}')
        if paragraphs:
            chapters.append((heading, paragraphs))
        if chapters:
            yield epub_path, get_title(epub_path), chapters
    if errors:
        for error in errors:
            print(error, file=stderr)
            exit(1)


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
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-b', '--bare', action='store_true', help='just output filenames')
    parser.add_argument('-n', '--no-wrap', action='store_true', help='do not word-wrap output')
    parser.add_argument('epub', type=Path, help='an epub file or a directory containing EPUB files')
    parser.add_argument('phrase', type=str, nargs='+', help='search phrases')
    args = parser.parse_args()

    try:
        for result in search(args.epub, args.string, args.no_wrap):
            show(result, args.bare)
    except FileNotFoundError:
        print(f'Not found: {repr(str(args.epub))}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main()

# end
