[ -z "$1" ] && { echo give the pdf source that must be printed as a booklet; exit 1 ; }
DB=$( basename $1 .book.pdf )
pdftops "$1" $DB.ps
psbook -s 16 < $DB.ps | psnup -pa4 -Pa4 -2 | pstops 2:0 > $DB.even.ps 
psbook -s 16 < $DB.ps | psnup -pa4 -Pa4 -2 | pstops 2:-1 > $DB.odd.ps


ps2pdf $DB.odd.ps 
ps2pdf $DB.even.ps

echo "Imprimer d'abord pair.pdf, puis impair.pdf sur les mêmes feuilles que vous aurez
bien positionnées"

