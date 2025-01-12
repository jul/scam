<style>
* {    font-family: sans-serif }
body { text-align: center;background:#f5f5ff; }
div, table { background:#f5f5ff;border-spacing:0;text-align:left;width:40em;margin:auto;border-radius:.5em;margin-bottom:1em;padding-left:.5em; }
tbody tr:nth-child(odd) {  background-color: #ccd;}
fieldset {margin:auto; box-shadow: 2px 2px 4px #113; border: 1px solid #666;  border-radius: .5em; width: 30em;  background:#eef; }

.spacer { width:40em; margin:auto;height:5em  }
.bandeau a:hover,select:hover, [type=submit]:hover { background:#117; color:white; border-radius:.5em; }
.bandeau { text-align:center;background:#f5f5ff;position:fixed;width:50em; z-index:1;top:0;margin-top:0; left:0; right:0; margin:auto;height:5em }
.bandeau a { padding:.4em;font-size:120%; font-weight:800; color:#117 }
:visited { color:#117 }
[type=submit] { cursor:pointer; box-shadow:1px 1px 2px #aaa }
embed { max-height:30em;min-height:20em; display:inline; }
form { text-align: left; display:inline-block; }
input,select { margin-bottom:1em; padding:.5em;} ::file-selector-button { padding:.5em}
input:not([type=file]) { border:1px solid #666; border-radius:.5em}
[nullable=false] { border:1px solid red !important;border-radius:.5em;}
[value=create], [value=reply] { background:#ffffba} [value=delete], [value=del] { background:#bae1ff}
[value=transition] { background: #ddf; }
[value=share] { background: #fbd; }
[value=update], [value=edit] { background:#ffdfda} [value=search] { background:#baffc9} 
[value=attach] { background: #efd }
[value=post] { background: #def; }
.hidden { display:none;}
textarea { resize:none }
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
