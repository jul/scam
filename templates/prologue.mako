<style>
* {    font-family: sans-serif }
body { text-align: center;background:white; }
div, table { background:white;border-spacing:0;text-align:left;width:30em;margin:auto;border-left:1px solid #666;border-radius:.5em;margin-bottom:1em;padding-left:.5em; }
tbody tr:nth-child(odd) {  background-color: #eee;}
fieldset { box-shadow: 3px 3px 3px #113; border: 1px solid #666;  border-radius: .5em; width: 30em; margin: auto; background:#eef; }

form { text-align: left; display:inline-block; }
input,select { margin-bottom:1em; padding:.5em;} ::file-selector-button { padding:.5em}
input:not([type=file]) { border:1px solid #666; border-radius:.5em}
[nullable=false] { border:1px solid red !important;border-radius:.5em;}
[value=create] { background:#ffffba} [value=delete] { background:#bae1ff}
[value=update] { background:#ffdfda} [value=search] { background:#baffc9} 
.hidden { display:none;}
[type=submit] { margin-right:1em; margin-bottom:0em; border:1px solid #333; padding:.5em; border-radius:.5em; }
</style>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
<script type="text/javascript" src=
"https://cdnjs.cloudflare.com/ajax/libs/jquery-cookie/1.4.1/jquery.cookie.min.js">
    </script>
    <script>

$(document).ready(() => {
    $("form").each((i,el) => {
        $(el).wrap("<fieldset></fieldset>"  );
        $(el).before("<legend>" + el.action + "</legend>");
        $(el).attr("enctype","multipart/form-data");
        $(el).attr("method","POST");
    });
    $("input:not([type=hidden],[type=submit]),select,textarea").each((i,el) => {
        $(el).before("<label>" + el.name+ "</label><br/>");
        $(el).after("<br>");
    });
});


</script>
