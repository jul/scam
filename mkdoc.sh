#!/usr/bin/env bash
<< =cut

=head1 NAME

mkdoc.sh

=head2 SYNOPSIS

Generates the book. Requires pandoc and xelatex for making the book

  DB=DB  ./mkdoc.sh

=cut
DB=${DB:-scam}


sqlite3 $DB 'select text || "
" from text where id = 1' > "assets/${DB}.titre.md"

sqlite3 $DB 'select "
" || text || "
" from text where id != 1 order by book_order ASC NULLS LAST, id ASC' > "assets/${DB}.body.md"
set -x
cd assets
pandoc "${DB}.body.md" -F ../graphviz.py -F pandoc-include -o "${DB}.body.gfm.md" 
pandoc "${DB}.body.gfm.md" -F ../add_link_list.py -o "${DB}.book.pdf.int.md"

cat "${DB}.titre.md" "${DB}.book.pdf.int.md" > "${DB}.book.pdf.md"
cat "${DB}.titre.md" "${DB}.body.gfm.md" > "${DB}.book.html.md"

pandoc "${DB}.book.html.md" --toc -c pandoc.css -so "${DB}.book.html"
pandoc "${DB}.book.pdf.md"  --toc --pdf-engine=xelatex  \
    -V documentclass=extreport   --variable fontsize=12pt \
    -V papersize=a4 \
    -so "${DB}.book.pdf"

cd ..
