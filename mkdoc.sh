#!/usr/bin/env bash
<< =cut

=head1 NAME

mkdoc.sh

=head2 SYNOPSIS

Generates the book. Requires pandoc and xelatex for making the book

  DB=DB  ./mkdoc.sh

=cut
DB=${DB:-scam.db}

sqlite3 $DB 'select text from title where id=1;' > assets/title.md
sqlite3 $DB 'select " " || text || " 
" from text order by book_order ASC NULLS LAST, id ASC' > assets/body.md

cd assets
pandoc -s body.md -f gfm  -o ./body.pdf.md
pandoc body.pdf.md -F ../add_link_list.py -o book.md
cat title.md book.md > book.pdf.md

pandoc ./book.pdf.md --lua-filter=../pagebreak.lua --toc -c pandoc.css -so "book.html"
pandoc book.pdf.md  --toc --pdf-engine=xelatex  --lua-filter=../pagebreak.lua \
    -V documentclass=extreport   --variable fontsize=12pt \
    -V papersize=a4 \
    -so book.pdf

cd ..
