#!/usr/bin/env bash
<< =cut

=head1 NAME

mkdoc.sh

=head2 SYNOPSIS

Generates the book. Requires pandoc and xelatex for making the book

  DB=DB  ./mkdoc.sh

=cut

set -x
DB=${DB:-scam}
PDF=${PDF:-}
TOC=${TOC:-"--toc"}

DB_SHORT=$( basename  $DB )


sqlite3 $DB 'select text || "
" from text  order by book_order ASC NULLS LAST, id ASC LIMIT 1' > "assets/${DB_SHORT}.titre.md"

sqlite3 $DB 'select "
" || text || "
" from text where text IS NOT NULL order by book_order ASC NULLS LAST, id ASC LIMIT -1 OFFSET 1 ' > "assets/${DB_SHORT}.body.md"

cd assets
pandoc "${DB_SHORT}.body.md" -F ../graphviz.py -F pandoc-include  -o "${DB_SHORT}.body.gfm.md" 
pandoc "${DB_SHORT}.body.gfm.md" -F ../add_link_list.py -o "${DB_SHORT}.book.pdf.int.md"

cat "${DB_SHORT}.titre.md" "${DB_SHORT}.book.pdf.int.md" > "${DB_SHORT}.book.pdf.md"
cat "${DB_SHORT}.titre.md" "${DB_SHORT}.body.gfm.md" > "${DB_SHORT}.book.html.md"

if [ ! -z "$PDF" ]; then
    pandoc "${DB_SHORT}.book.pdf.md"  $TOC --pdf-engine=xelatex  \
        -so "${DB_SHORT}.book.pdf"
else
    pandoc "${DB_SHORT}.book.html.md" --mathml $TOC \
        -c ./pandoc.css -so "${DB_SHORT}.book.html"
fi
cd ..

