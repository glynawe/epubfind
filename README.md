# Epubfind 

Epubfind searches for sets of phrases within an EPUB ebook, or within all every
ebook in a directory. 

A paragraph from an ebook matches if it contains all the search phrases. Those
matching paragraphs will be output. Groups of matching paragraphs will be given
book title and chapter headings so that they can be located in the book.

Search phrases are case-insensitive. A phrase can be a single word or a string
of several words in quotes. E.g. `'suddenly vanish away'`. The width of the
spacing between words is ignored. 

A phrase may also be a 
[regular expression](https://www.w3schools.com/python/python_regex.asp)
pattern. This is good when looking for alternatives. The pattern `'beamish|uffish'` 
will find paragraphs containing either "beamish" or "uffish".

Epubfind understands the inner structure of EPUB files, so it does a better job
of finding text than similar tools.


## Example

Let's look for some of the weird words in *The Hunting of the Snark* (since it
is in verse, we will use the `--no-wrap` output option):

    epubfind --no-wrap snark.epub 'beamish|uffish|galumphing|outgrabe' 

The output.

    ----------------------------------------------------------------------
    The Hunting of the Snark: An Agony in Eight Fits

    snark.epub
    ----------------------------------------------------------------------

    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    Fit the Third
    THE BAKER’S TALE
    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    “‘But oh, beamish nephew, beware of the day,
        If your Snark be a Boojum! For then
    You will softly and suddenly vanish away,
        And never be met with again!’

    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    Fit the fourth
    THE HUNTING
    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    The Bellman looked uffish, and wrinkled his brow.
        “If only you’d spoken before!
    It’s excessively awkward to mention it now,
        With the Snark, so to speak, at the door!

    The Beaver went simply galumphing about,
        At seeing the Butcher so shy:
    And even the Baker, though stupid and stout,
        Made an effort to wink with one eye.

    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    Fit the Fifth
    THE BEAVER’S LESSON
    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    The Beaver had counted with scrupulous care,
        Attending to every word:
    But it fairly lost heart, and outgrabe in despair,
        When the third repetition occurred.

## How it works

EPUBs are actually ZIP files containing directories of XHTML text files. This
script unzips and opens those XHTML files, uses the [lxml](https://lxml.de/)
XHTML processing package to extract heading and paragraph text, removes word
wrapping from the paragraphs, then searches them with a regular expression
derived from the search phrase.
