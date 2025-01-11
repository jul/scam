#!/usr/bin/env bash
<< =cut

=head1 NAME

mkdoc.sh

=head2 SYNOPSIS

Generates the book. Requires pandoc and xelatex for making the book

  DB=DB  ./mkdoc.sh

=cut
DB=${DB:-scam}

sqlite3 $DB 'select text from title where id=1;' > assets/title.md
sqlite3 $DB 'select "
" || text || "
" from text order by book_order ASC NULLS LAST, id ASC' > assets/body.md

cd assets
#pandoc -s body.md -f gfm  -o body.gfm.md
cp body.md body.gfm.md 
pandoc body.gfm.md -F ../add_link_list.py -o book.int.pdf.md
cat title.md book.int.pdf.md > book.pdf.md
cat title.md body.gfm.md > book.html.md


pandoc book.html.md --toc -c pandoc.css -so "${DB}.book.html"
pandoc book.pdf.md  --toc --pdf-engine=xelatex  \
    -V documentclass=extreport   --variable fontsize=12pt \
    -V papersize=a4 \
    -so "${DB}.book.pdf"

cd ..
