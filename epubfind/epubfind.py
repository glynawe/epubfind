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


from sys import stderr, exit
from importlib.util import find_spec
if not find_spec('lxml'):  # In case this script is used stand-alone.
    print(__doc__, file=stderr)
    print("*** EPUBFIND REQUIRES THE LXML LIBRARY: run 'pip3 install lxml'", file=stderr)
    exit(1)
from lxml import html, etree
from lxml.etree import ElementTree, Element
from urllib.parse import urljoin, urlparse, unquote
from typing import IO, NamedTuple, Iterator, Pattern, Iterable, Optional
from os import walk
from re import DOTALL, compile, sub, IGNORECASE
from zipfile import ZipFile
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from textwrap import wrap

def prettyprint(element, **kwargs):
    xml = etree.tostring(element, pretty_print=True, **kwargs)
    print(xml.decode(), end='')


def banner(headings: list[str], rule: str) -> None:
    s = '\n'.join(headings)
    print(f'\n{rule}\n{s}\n{rule}\n')


def wrap_text(text: str, width: int) -> str:
    return '\n'.join(wrap(text, width))


class Patterns:
    def __init__(self, phrases: list[str]) -> None:
        self.patterns: list[Pattern] = []
        for phrase in phrases:
            s = phrase.strip()
            s = sub(r'\s+', r'\\s+', s)  # spaces match any number of spaces
            s = r'\b' + s + r'\b'  # only full words get matched
            self.patterns.append(compile(s, IGNORECASE|DOTALL))
    def match(self, text: str) -> bool:
        return all(p.search(text) for p in self.patterns)


class Epub (ZipFile):
    opf_url: str
    opf: ElementTree
    spine: list[str]
    title: str
    filename: Path

    def __init__(self, path: Path) -> None:
        super().__init__(path, mode='r')

        container = self.read_xml('META-INF/container.xml')
        self.opf_url = str(self.xpath(container, '//container:rootfile/@full-path')[0])
        self.opf = self.read_xml(self.opf_url)

        elements = self.xpath(self.opf, '//dc:title')
        self.title = elements[0].text.strip() if elements else self.filename

        self.spine = []
        hrefs: dict[str,str] = dict()
        for node in self.xpath(self.opf, '//opf:item'):
            hrefs[node.attrib['id']] = node.attrib['href']
        for node in self.xpath(self.opf, '//opf:spine/opf:itemref'):
            idref = node.attrib['idref']
            self.spine.append(hrefs[idref])

    def read_html(self, url: str, base='') -> ElementTree:
        with self.open_url(url, base=(base or self.opf_url)) as file:
            return html.parse(file, parser=html.HTMLParser(encoding='utf-8'))

    def read_xml(self, url: str, base='file:///') -> ElementTree:
        with self.open_url(url, base) as file:
            return etree.parse(file)

    @staticmethod
    def zip_name(url: str, base: str) -> str:
        return unquote(urlparse(urljoin(base, url)).path).removeprefix('/')

    def open_url(self, url: str, base: str) -> IO[bytes]:
        return self.open(self.zip_name(url, base), mode='r')

    def xpath(self, doc: ElementTree, expression: str) -> list[Element]:
        return doc.xpath(expression, namespaces=self.NAMESPACES)

    NAMESPACES = {
        'dc': "http://purl.org/dc/elements/1.1/",
        'dcterms': "http://purl.org/dc/terms/",
        'opf': "http://www.idpf.org/2007/opf",
        'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}

    def search(self, patterns: Patterns) -> Optional['Result']:
        chapters: list[ChapterResult] = []
        paragraphs: list[Element] = []
        heading = self.title
        for url in self.spine:
            document = self.read_html(url, base=self.opf_url)
            for element in document.xpath('//p|//h1|//h2|//h3'):
                text = element.text_content()
                if element.tag != 'p':  # is a heading
                    if paragraphs or patterns.match(heading):
                        chapters.append(ChapterResult(heading, paragraphs))
                        paragraphs = []
                    heading = text
                elif patterns.match(text):
                    paragraphs.append(element)
        if paragraphs:
            chapters.append(ChapterResult(heading, paragraphs))
        return Result(self, chapters) if chapters else None


class Result(NamedTuple):
    epub: Epub
    chapter_results: list['ChapterResult']
    def show(self, bare: bool, no_wrap: bool, width=70) -> None:
        """ Display the search result for one EPUB in the terminal."""
        if bare:
            print(str(self.epub.filename))
        else:
            banner([self.epub.title, self.epub.filename], '-' * width)
            for chapter in self.chapter_results:
                chapter.show(no_wrap, width)


class ChapterResult(NamedTuple):
    heading: str
    paragraphs: list[Element]
    def show(self, no_wrap: bool, width: int) -> None:
        banner([self.heading], rule='- ' * (width//2))
        for p in self.paragraphs:
            text = p.text_content()
            print()
            print(text if no_wrap else wrap_text(text, width))


def files(path: Path, extensions: Iterable[str] = ()) -> Iterator[Path]:
    """Iterate through files in a directory path.
       (But if the path argument is a file then only yield that.)"""
    def has_extension(name: str) -> bool:
        return not extensions or any(name.endswith(e) for e in extensions)
    if path.is_file() and has_extension(path.name):
        yield path
    elif path.is_dir():
        for dir_path, _, filenames in walk(path):
            for filename in filenames:
                if has_extension(filename):
                    yield Path(dir_path, filename)
    else:
        raise FileNotFoundError()


def main():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-b', '--bare', action='store_true', help='just output filenames')
    parser.add_argument('-n', '--no-wrap', action='store_true', help='do not word-wrap output')
    parser.add_argument('-w', '--width', type=int, default=70, help='width of the output')
    parser.add_argument('epub', type=Path, help='an epub file or a directory containing EPUB files')
    parser.add_argument('phrase', type=str, nargs='+', help='search phrases')
    args = parser.parse_args()
    patterns = Patterns(args.phrase)
    errors = []
    for epub_path in files(args.epub, extensions=['.epub']):
        try:
            with Epub(epub_path) as epub:
                result = epub.search(patterns)
                if result:
                    result.show(args.bare, args.no_wrap, 70)
        except Exception as e:
            errors.append((epub_path, e))
    for path, exception in errors:
        quoted = repr(str(path))
        print(f'*** Error in {quoted}: {exception}')


if __name__ == '__main__':
    main()

# end
