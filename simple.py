import multipart
from wsgiref.simple_server import make_server
from json import dumps
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, String, Float, Date, DateTime,UnicodeText, ForeignKey
from html.parser import HTMLParser
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import select

from urllib.parse import parse_qsl, urlparse

engine = create_engine("postgresql://jul@192.168.1.32/pdca")
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
            if attrs["type"] in ("email", "url", "phone", "text"):
                self.cols += [ Column(attrs["name"], UnicodeText ), ]
            if attrs["type"] == "number":
                if attrs["step"] == "any":
                    self.cols+= [ Columns(attrs["name"], Float), ]
                else:
                    self.cols+= [ Column(attrs["name"], Integer), ]
            if attrs["type"] == "date":
                self.cols += [ Column(attrs["name"], Date) ]
            if attrs["type"] == "datetime":
                self.cols += [ Column(attrs["name"], DateTime) ]
            if attrs["type"] == "time":
                self.cols += [ Column(attrs["name"], Time) ]
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


router = dict({"" : lambda fo: """
<!doctype html>
<html>
<head>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
<script>
$(document).ready(function() {
    var model  = $("model").html();
    $("form").each((i,el) => {
        el._dom.value = model;
    });
    $("input:not([type=hidden],[type=submit])").each((i,el) => {
        $(el).before("<label>" + el.name+ "</label><br/>");
        $(el).after("<br>");
    });
    $("form").each((i,el) => {
        $(el).wrap("<fieldset>"+ el.action + "</fieldset>"  );
    })
});
</script>
</head>
<body>
<model>
<form action=/user  >
<input type=number name=id />
<input type=text name=name />
<input type=email name=email >
<input type=hidden name=_dom />
<input type=submit formmethod=post >
<input type=submit value=search formmethod=get />
</form>
<form action=/event name=toto method=GET >
<input type=number name=id />
<input type=date name=date />
<input type=text name=text />
<input type=number name=user_id />
<input type=hidden name=_dom />
<input type=submit value=insert formmethod=post />
<input type=submit value=search formmethod=get />
</form>
</model>
</body>
</html>
""",
})

def simple_app(environ, start_response):
    fo,fi=multipart.parse_form_data(environ)
    fo.update(**{ k: dict(
            name=fi.filename,
            content=fi.file.read().decode('utf-8', 'backslashreplace'),
            content_type =fi.content_type,
        ) for k,v in fi.items()})
    fo["_path"]=environ["PATH_INFO"]
    fo.update(**dict(parse_qsl(environ["QUERY_STRING"])))
    start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
    try:
        HTMLtoData().feed(fo.dict["_dom"][0])
    except KeyError: pass
    try:
        del fo.dict["_dom"]
    except KeyError: pass
    metadata = MetaData()
    metadata.reflect(bind=engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    table = environ["PATH_INFO"][1:]

    with Session(engine) as session:
        if table in tables.keys():
            Item = getattr(Base.classes, table)
            if environ.get("REQUEST_METHOD", "GET") == "POST" and table in tables.keys():
                new_item = Item(**{ k:v for k,v in fo.items() if v and not k.startswith("_")})
                session.add(new_item)
                ret=session.commit()
                fo["insert_result"] = new_item.id
            if environ.get("REQUEST_METHOD") == "GET" and table in tables.keys():
                result = []
                for elt in session.execute(
                    select(Item).filter_by(**{ k : v for k,v in fo.items() if v and not k.startswith("_")})).all():
                    result += [{ k.name:getattr(elt[0],k.name) for k  in tables[table].columns}]
                print(result)
                fo["search_result"] = result
    return [ router.get(fo['_path'][1:],lambda fo:dumps(fo.dict, indent=4, default=str))(fo).encode()]

print("Crudest CRDU of them all on port 5000...")
make_server('', 5000, simple_app).serve_forever()
