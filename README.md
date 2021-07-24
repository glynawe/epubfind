# Epubsearch 

This script searches for a string within all the EPUB ebooks in a directory tree. The titles and file names of the EPUBs that match, and their matching paragraphs, will be output. The search string is case-insensitive and ignores the width of spacing between words. The search string can be a regexp.

(EPUBs are actually ZIP files containing directories of XHTML text files. This script opens those XHTML files, uses the `lxml` XHTML processing package to extract heading and paragraph text, then searches that text with a regex derived from the search string.)

