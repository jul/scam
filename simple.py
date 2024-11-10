# STDLIB 
import multipart
from wsgiref.simple_server import make_server
from json import dumps
from html.parser import HTMLParser
from base64 import b64encode
from urllib.parse import parse_qsl, urlparse
import traceback
from  http.cookies import SimpleCookie as Cookie
from uuid import UUID as  UUIDM # conflict with sqlachemy
from datetime import datetime as dt, UTC
import sys
# external dependencies
# lightweight
from dateutil import parser
from time_uuid import TimeUUID
# NEEDS A BINARY INSTALL (scrypt)
from passlib.hash import scrypt as crypto_hash # we can change the hash easily
# heaviweight
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database


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
        self.enum =[]
        self.engine= engine
        self.meta = MetaData()
        super().__init__()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        simple_mapping = dict(
            email = UnicodeText, url = UnicodeText, phone = UnicodeText,
            text = UnicodeText, checkbox = Boolean, date = Date, time = Time,
            datetime = DateTime, file = Text, password = Text, uuid = Text, #UUID is postgres specific
        )
        if tag == "select":
            self.enum=[]
            self.current_col = attrs["name"]
        if tag == "option":
            self.enum += [ attrs["value"] ]
        if tag == "unique_constraint":
            self.cols += [    UniqueConstraint(*attrs["col"].split(','), name=attrs["name"]) ]
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
                self.cols += [ Column(attrs["name"], simple_mapping[attrs["type"]],
                nullable = [False, True][attrs.get("nullable", "true")=="true"],
                unique = [True, False][attrs.get("unique", "false")=="false"],

                )]
            if attrs["type"] == "number":
                if attrs["step"] == "any":
                    self.cols+= [ Columns(attrs["name"], Float), ]
                else:
                    self.cols+= [ Column(attrs["name"], Integer), ]
        if tag== "form":
            self.table = urlparse(attrs["action"]).path[1:]

    def handle_endtag(self, tag):
        if tag == "select":
            self.cols+= [ Column(self.current_col,Enum(*[(k,k) for k in self.enum]))]
            self.current_col=None
            self.enum = []
        if tag=="form":
            self.tables += [ Table(self.table, self.meta, *self.cols), ]
            tables[self.table] = self.tables[-1]
            self.table = ""
            self.cols = []
            with engine.connect() as cnx:
                self.meta.create_all(engine)
                cnx.commit()
prologue = """
<style>
* {    font-family:"Sans Serif" }
body { text-align: center; }
div, table {border-spacing:0;text-align:left;width:30em;margin:auto;border:1px solid #666;border-radius:.5em;margin-bottom:1em; }
tbody tr:nth-child(odd) {  background-color: #eee;}
fieldset {  border: 1px solid #666;  border-radius: .5em; width: 30em; margin: auto; }
form { text-align: left; display:inline-block; }
input,select { margin-bottom:1em; padding:.5em;} ::file-selector-button { padding:.5em}
input:not([type=file]) { border:1px solid #666; border-radius:.5em}
[nullable=false] { border:1px solid red !important;}
[value=create] { background:#ffffba} [value=delete] { background:#bae1ff}
[value=update] { background:#ffdfda} [value=search] { background:#baffc9}
[type=submit] { margin-right:1em; margin-bottom:0em; border:1px solid #333; padding:.5em; border-radius:.5em; }
</style>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
<script type="text/javascript" src=
"https://cdnjs.cloudflare.com/ajax/libs/jquery-cookie/1.4.1/jquery.cookie.min.js">
    </script>


"""
model="""
    <form  action=/user >
        <input type=number name=id />
        <input type=file name=pic_file />
        <input type=text name=name nullable=false unique=true />
        <input type=checkbox name=is_checked />
        <select name="prefered_pet" >
            <option value="">Please select an item</option>
            <option value="dog">Dog</option>
            <option value="cat">Cat</option>
            <option value="hamster">Hamster</option>
            <option value="spider">Spider</option>
        </select>
        <input type=email name=email nullable=false />
        <input type=password name=password nullable=false />
        <input type=uuid name=token nullable=true />
        <unique_constraint col=email name=email_unique ></unique_constraint>
    </form>
    <form action=/group >
        <input type=number name=id />
        <input type=text name=name />
    </form>
    <form action=/user_group >
        <input type=number name=id />
        <input type=number name=group_id nullable=false />
        <input type=number name=user_id nullable=false />
        <unique_constraint col=user_id,group_id name=unique_group_id ></unique_constraint>

    </form>
    <form action=/event  >
        <input type=number name=id />
        <input type=date name=from_date nullable=false />
        <input type=date name=to_date nullable=false />
        <input type=text name=text nullable=false />
        <input type=number name=group_id nullable=false />
    </form>
"""
html = f"""
<!doctype html>
<html>
<head>
{prologue}
<script>

$(document).ready(function() {{
    $("form").each((i,el) => {{
        $(el).wrap("<fieldset></fieldset>"  );
        $(el).before("<legend>" + el.action + "</legend>");
        $(el).append("<input name=_action type=submit value=create ><input name=_action type=submit value=search >")
        $(el).append("<input name=_action type=submit value=update ><input name=_action type=submit value=delete >")
        $(el).attr("enctype","multipart/form-data");
        $(el).attr("method","POST");
    }});
    $("input:not([type=hidden],[type=submit]),select").each((i,el) => {{
        $(el).before("<label>" + el.name+ "</label><br/>");
        $(el).after("<br>");
    }});
}});
</script>
</head>
<body >
<div><ul>
    <li>try <a href=/login >here to get granted the authorization to use update/delete action</a></li>
    <li>try <a href=/user_view?id=1 > here once you filled in your first user</a></li>
    <li>try <a href=/user_view> here is a list of all known users</a></li>
</ul></div>
{model}
</body>
</html>
"""


router = dict({"" : lambda fo: html,
    "login" : lambda fo : f"""
<!doctype html>
<html>
<head>
{prologue}
<script>

$(document).ready(function() {{
    $("form").each((i,el) => {{
        $(el).wrap("<fieldset></fieldset>"  );
        $(el).before("<legend>" + el.action + "</legend>");
        $(el).attr("enctype","multipart/form-data");
        $(el).attr("method","POST");
    }});
    $("input:not([type=hidden],[type=submit]),select").each((i,el) => {{
        $(el).before("<label>" + el.name+ "</label><br/>");
        $(el).after("<br>");
    }});
}});
</script>
</head>
<form action=/grant >
<input type=text name=email>
<input type=password name=password>
<input type=submit name=_action value=grant >
</form>
""",
    "user_view" : lambda fo : f"""
<!doctype html>
<html>
<head>
{prologue}
<script>
    $.ajax({{
        url: "/user",
        method: "POST",
        data : {{ {fo.get("id") and 'id:"%s",' % fo["id"] or "" } _action: "read"}}
    }}).done((msg) => {{
    for (var i=1; i<msg['result'][0].length;i++) {{
        $($("[name=toclone]")[0]).after($("[name=toclone]")[0].outerHTML);
    }}
    msg["result"][0].forEach((res,i) => {{
        $("span", $($("[name=toclone]")[i])).each( (h,el) => {{
            $(el).text(res[$(el).attr("name")]);
        }})
        $("[name=pic]", $($("[name=toclone]")[i])).attr("src",res["pic_file"]);
    }})
}});
</script>
</head>
<body>
<table name=toclone >
    <tr><td><label>id</label>:</td><td> <span name=id /></td></tr>
    <tr><td><label>name</label>:</td><td> <span name=name /></td></tr>
    <tr><td><label>email</label>:</td><td> <span name=email /></td></tr>
    <tr><td><label>prefered pet</label>:</td><td><span name=prefered_pet /></td></tr>
    <tr><td><label>is checked </label>:</td><td><span name=is_checked /></td></tr>
    <tr><td><label>token </label>:</td><td><span name=token /></td></tr>
    <tr><td><label>picture</label>:</td><td><img width=200px name=pic ></td></tr>
</table>
</body>
</html>
"""})

#helpers
def redirect(to):
    start_response('302 Found', [('Location',f"{to}")])
    return [ f"""<html><head><meta http-equiv="refresh" content="0; url="{to}"</head></html>""".encode() ]

def log(msg, ln=0, context={}):
    print("LN:%s : CTX: %s : %s" % (ln, context, msg), file=sys.stderr)

line = lambda : sys._getframe(1).f_lineno

def simple_app(environ, start_response):
    fo, fi=multipart.parse_form_data(environ)
    fo.update(**{ k: dict(
            name=fi[k].filename,
            content_type=fi[k].content_type,
            content=b64encode(fi[k].file.read())
        ) for k,v in fi.items()})
    table = route = environ["PATH_INFO"][1:]
    fo.update(**dict(parse_qsl(environ["QUERY_STRING"])))
    try:
        fo["_token"] = Cookie(environ["HTTP_COOKIE"])["Token"].value
    except:
        log("no cookie found", ln=line())
    HTMLtoData().feed(model)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    Base = automap_base(metadata=metadata)
    Base.prepare()
    form_to_db = lambda attrs : {  k: (
                    # handling of input having date/time in the name
                    "date" in k or "time" in k and v and type(k) == str )
                        and parser.parse(v) or
                    # handling of input type = form havin "file" in the name of the inpur
                    "file" in k and f"""data:{fo[k]["content_type"]}; base64, {fo[k]["content"].decode()}""" or
                    # handling of boolean mapping which input begins with "is_"
                    k.startswith("is_") and [False, True][v == "on"] or
                    # password ?
                    k == "password" and crypto_hash.hash(v) or
                    v
                    for k,v in attrs.items() if v and not k.startswith("_")
    }
    action = fo.get("_action", "")
    def validate(fo):
        with Session(engine) as session:
            User = Base.classes.user
            try:
                user = session.scalars(select(User).where(User.token==fo["_token"])).one()
                log(dt.now() - TimeUUID(bytes=UUIDM("{%s}" % fo["_token"]).bytes).get_datetime(), ln=line(), context=fo)
                return False
            except Exception as e:
                log(traceback.format_exc(), ln=line(), context=fo)
                start_response('302 Found', [('Location',"/login?_redirect=/")], )
                return [ f"""<html><head><meta http-equiv="refresh" content="0; url="/login?_redirect=/</head></html>""".encode() ]

    if action=="grant":
        with Session(engine) as session:
            User = Base.classes.user
            user = session.scalars(select(User).where(User.email==fo["email"])).one()
            user.token = str(TimeUUID.with_utcnow())
            fo["validate"] = crypto_hash.verify(fo["password"], user.password)
            session.flush()
            session.commit()
            if fo["validate"]:
                start_response('302 Found', [('Location',"/"),('Set-Cookie', "Token=%s" % user.token)], )
                return [ f"""<html><head><meta http-equiv="refresh" content="0; url="{fo.get("_redirect","/")}")</head></html>""".encode() ]

    has_error=False
    if route in tables.keys():
        with Session(engine) as session:
            try:
                Item = getattr(Base.classes, table)
                if action == "delete":
                    fo["_redirect"]= "delete"
                    if fail := validate(fo):
                        return fail
                    session.delete(session.get(Item, fo["id"]))
                    session.commit()
                    fo["result"] = "deleted"
                if action == "create":
                    new_item = Item(**form_to_db(fo))
                    session.add(new_item)
                    session.flush()
                    ret=session.commit()
                    fo["result"] = new_item.id
                    if table == "user":
                        return redirect("/user_view?id=%s" % new_item.id)

                if action == "update":
                    fo["_redirect"]= "update"
                    if fail:= validate(fo):
                        return fail
                    item = session.scalars(select(Item).where(Item.id==fo["id"])).one()
                    for k,v in form_to_db(fo).items():
                        setattr(item,k,v)
                    session.commit()
                    fo["result"] = item.id
                    if table == "user":
                        return redirect("/user_view?id=%s" % item.id)
                if action in { "read", "search" }:
                    result = []
                    for elt in session.execute(
                        select(Item).filter_by(**form_to_db(fo))).all():
                        result += [{ k.name:getattr(elt[0], k.name) for k in tables[table].columns},]
                    fo["result"] = result
            except Exception as e:
                has_error = True
                fo["error"] = e
                log(traceback.format_exc(), ln=line(), context=fo)
                session.rollback()
            if not has_error:
                start_response('200 OK', [('Content-type', 'application/json; charset=utf-8')])
                return [ dumps(fo.dict, indent=4, default=str).encode() ]
    start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
    return [ router.get(route,lambda fo:dumps(fo.dict, indent=4, default=str))(fo).encode() ]


print("Crudest CRUD of them all on port 5000...")
make_server('', 5000, simple_app).serve_forever()
