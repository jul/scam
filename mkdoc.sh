#!/usr/bin/env bash
<< =cut

=head1 NAME

mkdoc.sh

=head2 SYNOPSIS

Generates the book. Requires pandoc and xelatex for making the book

  DB=DB  ./mkdoc.sh

=cut
DB=${DB:-scam}
PDF=${PDF:-}


sqlite3 $DB 'select text || "
" from text  order by book_order ASC NULLS LAST, id ASC LIMIT 1' > "assets/${DB}.titre.md"

sqlite3 $DB 'select "
" || text || "
" from text where text IS NOT NULL order by book_order ASC NULLS LAST, id ASC LIMIT -1 OFFSET 1 ' > "assets/${DB}.body.md"
cd assets
pandoc "${DB}.body.md" -F ../graphviz.py -F pandoc-include -o "${DB}.body.gfm.md" 
pandoc "${DB}.body.gfm.md" -F ../add_link_list.py -o "${DB}.book.pdf.int.md"

cat "${DB}.titre.md" "${DB}.book.pdf.int.md" > "${DB}.book.pdf.md"
cat "${DB}.titre.md" "${DB}.body.gfm.md" > "${DB}.book.html.md"

pandoc "${DB}.book.html.md" --toc -c pandoc.css -so "${DB}.book.html"
if [ ! -z "$PDF" ]; then
pandoc "${DB}.book.pdf.md"  --toc --pdf-engine=xelatex  \
    -so "${DB}.book.pdf"
fi

cd ..
