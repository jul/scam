<!DOCTYPE html>
<html>
<head>
<%include file="prologue.mako" />
<%block name="include_head" />
</head>
<body >
<div class=bandeau  >
    <a class=graph href=/svg>Graph</a> /
    <a class=book href=/book>HTML</a> /
    <a class=pdf href=/pdf>(slow) PDF</a> /
    <a class=CRUD href=/model>REST API</a>

</div>
<div class=spacer >
</div>
${self.body() }
</body>
</html>

