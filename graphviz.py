#!/usr/bin/env python

"""
Pandoc filter to process code blocks with class "graphviz" into
graphviz-generated images.
"""

import hashlib
import os
import sys
from panflute import toJSONFilter, Str, Para, Image, CodeBlock



def sha1(x):
    return hashlib.sha1(x.encode(sys.getfilesystemencoding())).hexdigest()

imagedir = "."


def graphviz(elem, doc):
    if type(elem) == CodeBlock and 'graphviz' in elem.classes:
        code = elem.text
        sha1_code = sha1(code)
        with open(sha1_code, "wt") as f:
            f.write(code)
        os.system(f"dot {sha1_code} -T png > '{sha1_code}.png' ")
        filename = sha1(code)
        filetype = {'html': 'png', 'latex': 'pdf'}.get(doc.format, 'png')
        src = imagedir + '/dot.' + filename + '.' + filetype
        if not os.path.isfile(src):
            sys.stderr.write('Created image ' + src + '\n')
        return Para(Image(Str(""), url=filename + ".png", title=''))


if __name__ == "__main__":
    toJSONFilter(graphviz)
