import multipart
from wsgiref.simple_server import make_server
from json import dumps
from sqlalchemy import *
from html.parser import HTMLParser
from base64 import b64encode
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from dateutil import parser
from sqlalchemy_utils import database_exists, create_database
from urllib.parse import parse_qsl, urlparse

engine = create_engine("sqlite:///this.db")
if not database_exists(engine.url):
    create_database(engine.url)

tables = dict()

class HTMLtoData(HTMLParser):
    def __init__(self):
        global engine, tables
        self.cols = []
        self.table = ""
        self.tables= []
        self.engine= engine
        self.meta = MetaData()
        super().__init__()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        simple_mapping = dict(
            email = UnicodeText, url = UnicodeText, phone = UnicodeText, text = UnicodeText,
            date = Date, time = Time, datetime = DateTime, file = Text
        )
        if tag == "input":
            if attrs.get("name") == "id":
                self.cols += [ Column('id', Integer, primary_key = True), ]
                return
            try:
                if attrs.get("name").endswith("_id"):
                    table,_=attrs.get("name").split("_")
                    self.cols += [ Column(attrs["name"], Integer, ForeignKey(table + ".id")) ]
                    return
            except Exception as e: print(e)

            if attrs.get("type") in simple_mapping.keys():
                self.cols += [ Column(attrs["name"], simple_mapping[attrs["type"]]), ]

            if attrs["type"] == "number":
                if attrs["step"] == "any":
                    self.cols+= [ Columns(attrs["name"], Float), ]
                else:
                    self.cols+= [ Column(attrs["name"], Integer), ]
        if tag== "form":
            self.table = urlparse(attrs["action"]).path[1:]

    def handle_endtag(self, tag):
        if tag=="form":
            self.tables += [ Table(self.table, self.meta, *self.cols), ]
            tables[self.table] = self.tables[-1]
            self.table = ""
            self.cols = []
            with engine.connect() as cnx:
                self.meta.create_all(engine)
                cnx.commit()
html = """
<!doctype html>
<html>
<head>
<style>
* {    font-family:"Sans Serif" }
body { text-align: center; }
fieldset {  border: 1px solid #666;  border-radius: .5em; width: 30em; margin: auto; }
form { text-align: left; display:inline-block; }
input { margin-bottom:1em; padding:.5em;}
[value=create] { background:#ffffba} [value=delete] { background:#bae1ff} [value=update] { background:#ffdfda}
[value=read] { background:#baffc9}
[type=submit] { margin-right:1em; margin-bottom:0em; border:1px solid #333; padding:.5em; border-radius:.5em; }
</style>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
<script>
$(document).ready(function() {
    $("form").each((i,el) => {
        $(el).wrap("<fieldset></fieldset>"  );
        $(el).before("<legend>" + el.action + "</legend>");
        $(el).append("<input name=_action type=submit value=create ><input name=_action type=submit value=read >")
        $(el).append("<input name=_action type=submit value=update ><input name=_action type=submit value=delete >")
        $(el).attr("enctype","multipart/form-data");
        $(el).attr("method","POST");

    });
    $("input:not([type=hidden],[type=submit])").each((i,el) => {
        $(el).before("<label>" + el.name+ "</label><br/>");
        $(el).after("<br>");
    });
    $.ajax({
        url: "/user",
        method: "POST",
        data : { id: 1, _action: "read"}
    }).done((msg) => {
        $("[name=test]").attr("src", "data:image/jpeg;base64, " +  msg["result"][0][0]["pic_file"])
    });
});
</script>
</head>
<body >
    <img name=test width=300px />
    <form  action=/user >
        <input type=number name=id />
        <input type=file name=pic_file />
        <input type=text name=name />
        <input type=email name=email />
    </form>
    <form action=/event  >
        <input type=number name=id />
        <input type=date name=from_date />
        <input type=date name=to_date />
        <input type=text name=text />
        <input type=number name=user_id />
    </form>
    </body>
</html>
"""


router = dict({"" : lambda fo: html,})

def simple_app(environ, start_response):
    fo, fi=multipart.parse_form_data(environ)
    print(fo)
    fo.update(**{ k: dict(
            name=fi[k].filename,
            content=b64encode(fi[k].file.read())
        ) for k,v in fi.items()})

    table = route = environ["PATH_INFO"][1:]
    fo.update(**dict(parse_qsl(environ["QUERY_STRING"])))
    HTMLtoData().feed(html)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    attrs_to_dict = lambda attrs : {  k: (
                    "date" in k or "time" in k ) and type(k) == str
                        and parser.parse(v) or
                    "file" in k and fo[k]["content"].decode() or v
                    for k,v in attrs.items() if v and not k.startswith("_")
    }
    if route in tables.keys():
        start_response('200 OK', [('Content-type', 'application/json; charset=utf-8')])
        with Session(engine) as session:
            try:
                action = fo.get("_action", "")
                Item = getattr(Base.classes, table)
                if action == "delete":
                    session.delete(session.get(Item, fo["id"]))
                    session.commit()
                    fo["result"] = "deleted"
                if action == "create":
                    new_item = Item(**attrs_to_dict(fo))
                    session.add(new_item)
                    session.flush()
                    ret=session.commit()
                    fo["result"] = new_item.id
                if action == "update":
                    session.delete(session.get(Item, fo["id"]))
                    new_item = Item(**attrs_to_dict(fo))
                    session.add(new_item)
                    session.commit()
                    fo["result"] = new_item.id
                if action in { "read", "search" }:
                    result = []
                    for elt in session.execute(
                        select(Item).filter_by(**attrs_to_dict(fo))).all():
                        result += [{ k.name:getattr(elt[0], k.name) for k in tables[table].columns}]
                    fo["result"] = result
            except Exception as e:
                fo["error"] = e
                session.rollback()
    else:
        start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])

    return [ router.get(route,lambda fo:dumps(fo.dict, indent=4, default=str))(fo).encode() ]

print("Crudest CRUD of them all on port 5000...")
make_server('', 5000, simple_app).serve_forever()
