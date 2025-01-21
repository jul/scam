#!/usr/bin/env python

import re
from sys import argv
from base64 import b64encode as b

in_html=argv[1]


css=re.compile(r'''.*<link.*href="(?P<src>[^"]*)".*''',re.M|re.S)
img=re.compile(r'''(.*<img .*src=")([^"]*)(".*)''', re.M|re.S)

for l in open(in_html, "rt"):
    if m := css.findall(l):
        print(f"""<style>
 {open(m[0],"rt").read()}
 </style>""")
    else:
        if m := img.match(l):
            print(m.group(1) + "data:image/toto;base64,", end="")
            print(b(open(m.group(2),"rb").read()).decode(),end='"')
            print(m.group(3))
        else:
            print(l, end='')


