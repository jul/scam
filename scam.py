#!/usr/bin/env python
# STDLIB 
import multipart
from wsgiref.simple_server import make_server
import re
from json import dumps, loads
from html.parser import HTMLParser
from base64 import b64encode, b64decode
from urllib.parse import parse_qsl, urlparse
from os import chdir
from subprocess import run, PIPE
from urllib.parse import unquote, quote
import traceback
from  http.cookies import SimpleCookie as Cookie
from uuid import UUID as  UUIDM # conflict with sqlachemy
from datetime import datetime as dt, UTC, timezone
import sys
from zlib import adler32
import os
# external dependencies
# lightweight
import magic
from archery import mdict
from filelock import FileLock
from dateutil import parser
from time_uuid import TimeUUID
# NEEDS A BINARY INSTALL (scrypt)
from passlib.hash import scrypt as crypto_hash # we can change the hash easily
# heavyweight
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from mako.template import Template
from mako.lookup import TemplateLookup



__DIR__= os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get('DB','scam')
DB_SHORT=os.path.basename(DB)
PORT=int(os.environ.get('PORT','5000'))
DB_DRIVER=os.environ.get('DB_DRIVER','sqlite')
DSN=f"{DB_DRIVER}://{DB_DRIVER == 'sqlite' and not DB.startswith('/') and '/' or ''}{DB}"

engine = create_engine(DSN)
if not database_exists(engine.url):
    create_database(engine.url)


tables = dict()
transtype_true = lambda p : (p[0],[False,True][p[1]=="true"])
def dispatch(p):
    return dict(
        nullable=transtype_true,
        unique=transtype_true,
        default=lambda p:("server_default",eval(p[1])),
    ).get(p[0], lambda *a:None)(p)

transtype_input = lambda attrs: dict(
    filter(lambda x :x, map(dispatch, attrs.items()))
)

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
        simple_mapping = {
            "email": UnicodeText, "url": UnicodeText, "phone": UnicodeText,
            "text": UnicodeText, "checkbox": Boolean, "date": Date, 
            "time": Time, "datetime-local": DateTime, "file": Text,
            "password" : Text, "uuid" : Text, #UUID is postgres specific
        }

        if tag in {"select", "textarea"}:
            self.enum=[]
            self.current_col=attrs["name"]
            self.attrs=attrs
        if tag == "option":
            self.enum.append( attrs["value"] )
        if tag == "unique_constraint":
            self.cols.append(UniqueConstraint(
                *attrs["col"].split(','), name=attrs["name"])
            )
        if tag in { "input" }:
            if attrs.get("name") == "id":
                additional = attrs.get("ondelete") \
                    and {"ondelete": attrs["ondelete"]} \
                    or dict()
                additional_col = dict(primary_key=True) | transtype_input(attrs)
                if "reference" in attrs:
                    self.cols.append(
                        Column(
                            attrs["name"], Integer,
                            ForeignKey(attrs["reference"], **additional),
                            **additional_col)
                    )
                else:
                    self.cols.append(
                        Column(
                            attrs["name"], Integer,
                            **additional_col)
                    )
                return
            if attrs.get("name").endswith("_id"):
                table=attrs.get("name").split("_")
                additional = attrs.get("ondelete") \
                    and {"ondelete": attrs["ondelete"]} \
                    or dict()
                additional_col = transtype_input(attrs)
                self.cols.append(
                    Column(
                        attrs["name"], Integer,
                        ForeignKey(attrs["reference"], **additional),
                        **additional_col)
                )
                return

            if attrs.get("type") in simple_mapping.keys() or tag in {"select",}:
                self.cols.append( 
                    Column(
                        attrs["name"], simple_mapping[attrs["type"]],
                        **transtype_input(attrs)
                    )
                )
            if attrs["type"] == "number":
                if attrs.get("step","") == "any":
                    self.cols.append( Columns(attrs["name"], Float) )
                else:
                    self.cols.append( Column(attrs["name"], Integer) )
        if tag== "form":
            self.table = urlparse(attrs["action"]).path[1:]

    def handle_endtag(self, tag):
        if tag == "select":
            # self.cols.append( Column(self.current_col,Enum(*[(k,k) for k in self.enum]), **transtype_input(self.attrs)) )

            self.cols.append( Column(self.current_col, Text, **transtype_input(self.attrs)) )
            
        if tag == "textarea":
            self.cols.append(
                Column(
                    self.current_col,
                    String(int(self.attrs["cols"])*int(self.attrs["rows"])),
                    **transtype_input(self.attrs)) 
           )
        if tag=="form":
            self.tables.append( Table(self.table, self.meta, *self.cols), )
            tables[self.table] = self.tables[-1]
            self.cols = []
            with engine.connect() as cnx:
                self.meta.create_all(engine)
                cnx.commit()


#helpers

def log(msg, ln=0, context={}):
    print("LN:%s : CTX: %s : %s" % (ln, context, msg), file=sys.stderr)

line = lambda : sys._getframe(1).f_lineno
log(f"connecting {DSN}", ln=line())

# single page app python part

def simple_app(environ, start_response):
    def redirect(to):
        start_response('302 Found', [('Location',f"{to}")])
        return [ f"""<html><head><meta http-equiv="refresh" content="0; url="{to}"</head></html>""".encode() ]

    fo, fi=multipart.parse_form_data(environ)
    fo.update(**{ k: dict(
            name=fi[k].filename,
            content_type=fi[k].content_type,
            content=b64encode(fi[k].file.read())
        ) for k,v in fi.items()})

    table = route = environ["PATH_INFO"][1:]
    here = environ["PATH_INFO"][0]

    fo.update(**dict(parse_qsl(environ["QUERY_STRING"])))
        
    env = TemplateLookup(directories=['./'])
    model = Template(filename="templates/model.mako",lookup=env).render(
        fo= { k:v for k,v in fo.dict.items() if "secret" not in k}
    )

    HTMLtoData().feed(model)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    Base = automap_base(metadata=metadata)
    Base.prepare()
    fo["_model"] = version = adler32(model.encode())
    dest=os.path.join(__DIR__, "assets",'diag.%s.png' % version)
    
    if not os.path.isfile(dest):
        os.system(os.path.join(__DIR__, "generate_diagram.py") + " " + DSN);
        os.system("dot out.dot -T png >  " + dest);

    potential_file = os.path.join(__DIR__, "assets", route )
    log(route, ln=line())
    if not os.path.isfile(potential_file ):
        log(DB, ln=line())
        if m:=re.compile(r'' + DB_SHORT + r'''\.annexe\.(\d+)$''').match(route):
            log("bing", ln=line())
            with engine.connect() as cnx:
                from sqlalchemy import text
                _id=m.group(1)
                for s in cnx.execute(text(f"""select annexe_file from annexe where id= :id"""), dict(id=_id)):
                    with open(f"assets/{DB_SHORT}.annexe.{_id}", "bw") as f:
                        f.write(b64decode(re.match(".*;base64,(.*)$", s[0]).group(1)))
                else:
                    start_response('200 OK', [('content-type', 'text/html; charset=utf-8')])
                    return [ b"" ]


    if os.path.isfile(potential_file ):
## python-magic
        start_response('200 OK', [('content-type',
            potential_file.endswith(".css") and "text/css"
            or magic.from_file(potential_file, mime=True) + ' ;charset=utf-8'), ])
        log(magic.from_file(potential_file, mime=True), ln=line())
        return [ open(potential_file, "rb").read() ]


    form_to_db = lambda attrs : {  k: (
        # handling of input having date/time in the name
        "date" in k or "time" in k and v and type(k) == str )
            and parser.parse(v) or
        # handling of input type = form havin "file" in the name of the inpur
        "file" in k \
            and open(f"""./assets/{DB_SHORT}.{table}.{fo["id"]}""", "wb").write(b64decode(fo[k]["content"])) \
            and f"""data:{fo[k]["content_type"]};base64,{fo[k]["content"].decode()}""" or

        # handling of boolean mapping which input begins with "is_"
        k.startswith("is_") and [False, True][v == "on"] or
        # password ?
        "password" in k and crypto_hash.hash(v) or
        v
        for k,v in attrs.items() if v != "" and not k.startswith("_")
    }
    action = fo.get("_action", "")

    fo["_user_id"]=1
    fo["_DB"] = DB_SHORT
    fo["_pics"] = []
    fo["_name"] =  'jul'

    if "_action" in fo and route in tables.keys():
        with Session(engine) as session:
            try:
                Item = getattr(Base.classes, table)
                if action == "delete":
                    try:
                        session.delete(session.get(Item, fo["id"]))
                        session.commit()
                        log("panpan")
                        fo["result"] = "deleted"
                        if table == "annexe":
                            log("femme de ménage")
                            os.system(f"""rm "assets/{DB_SHORT}.annexe.{fo["id"]}" """)
                    except Exception as e:
                        log(e)
                        fo["result"] = e
                if action == "create":
                    new_item = Item(**form_to_db(fo))
                    ret=0
                    try:
                        session.add(new_item)
                        ret=session.commit()
                        log(ret, ln=line())
                    except:
                        session.rollback()
                        log("pan", ln=line())
                        session.merge(new_item)
                        session.commit()
                    fo["result"] = ret

                if action == "update":
                    try:
                        item = session.scalars(select(Item).where(Item.id==fo["id"])).one()
                        log(item)
                        log(fo)
                        for k,v in form_to_db(fo).items():
                            setattr(item,k,v)
                        session.commit()
                        fo["result"] = item.id
                    except Exception as e:
                        log("upsert")
                        log("n" * 80)
                        session.rollback()
                        new_item = Item(**form_to_db(fo))
                        session.add(new_item)
                        ret=session.commit()


                if action in { "search" }:
                    result = []
                    for elt in session.execute(
                        select(Item).filter_by(**form_to_db(fo))).all():
                        result.append({ k.name:getattr(elt[0], k.name) for k in tables[table].columns})
                    fo["result"] = result
            except Exception as e:
                fo["error"] = e
                log(traceback.format_exc(), ln=line() )
                session.rollback()
            if to:=fo.get("_redirect"):
                log("redirect caught %s " % to)
                return redirect(to)
            start_response('200 OK', [('Content-type', 'application/json; charset=utf-8')])
            return [ dumps({k:v for k,v in fo.dict.items() if "secret" not in k}, indent=4, default=str).encode() ]
    if route =="":
        route="svg"
    if route == "model":
        route="index"
    to_write=""
    if m:=re.match(f"""{DB_SHORT}\\.(\\d+)\\.html""", route) :
        if not os.path.isfile(os.path.join("assets", route)):
            route="doc"
            fo["id"] = m.group(1)
            log(fo["id"], ln=line())
            with engine.connect() as cnx:
                from sqlalchemy import text
                for s in cnx.execute(text("""select text from text where id = :id"""), dict(id=fo["id"])):
                    fo["text"] = quote(s[0])
    if route == "doc" :
        os.chdir("assets")
        run([ "pandoc", "-" , "--standalone", "--mathml", "-s", "-F", os.path.join(__DIR__,"graphviz.py"), "-F", "pandoc-include", "-c" ,"pandoc.css","--metadata", "title=",  "-o" ,f"""./{DB_SHORT}.{fo["id"]}.html""" ], input=unquote(fo.get("text","")).encode(), stdout=PIPE)
        os.chdir("..")
        start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
        return [ open(f"""./assets/{DB_SHORT}.{fo["id"]}.html""", "rt").read().encode() ]
    
    if route == "order":
        res = []
        with engine.connect() as cnx:
            from sqlalchemy import text
            for s in cnx.execute(text("""select id from text where text is NOT NULL order by book_order ASC NULLS LAST, id ASC""")):
                res += s
        fo["_text_order"] = res

        # return in fo["_next"] next text by book order else actual_one+1
# https://stackoverflow.com/questions/2184043/sqlite-select-next-and-previous-row-based-on-a-where-clause

    log("srs?")
    if route == "book":
        log(f"DB={DB}", ln = line())
        os.system(f"""DB={DB} PDF= ./mkdoc.sh""")
        os.system(f"""cd assets && ../filter.py "{DB_SHORT}.book.html" > "{DB_SHORT}.book.shtml" """)

    if route == "pdf":
        os.system(f"""DB={DB} PDF=1 ./mkdoc.sh""")

    if route == "svg":
        with FileLock('out.dot.lock'):
            os.system(f"python ./generate_state_diagram.py {DSN} > out.dot ;dot -Tsvg out.dot > diag2.svg; ")
    
    if route == "comment":
        stack=dict()
        transition=[]
        seen = set([])
        todo = set([])
        fo["result"] = []
        with engine.connect() as cnx:
            if id := fo.get("id"):
                from sqlalchemy import text
                for s in cnx.execute(text("""select id, message, factoid, category, comment_id, user_id from comment where comment.id IN (
            with recursive is_fin(b) as
                (
                    SELECT :id
                    UNION
                    select id
                    from comment JOIN  is_fin
                    ON comment.comment_id=is_fin.b
               ) SELECT id FROM comment where id in is_fin )
                    """),dict(id=id)):
                    id, message, factoid, category, comment_id,user_id= s
                    stack[id] = dict(
                        message=message,id=id,user_id=user_id,
                        category=category, factoid=factoid, comment_id= comment_id
                    ) 
            else:
                from sqlalchemy import text 
                for s in cnx.execute(text("select id, message, factoid, category, comment_id, user_id from comment order by created_at_time ASC")):
                    id, message, factoid, category, comment_id,user_id= s
                    log(id, ln=line())
                    stack[id] = dict(
                        message=message,id=id,user_id=user_id,
                        category=category, factoid=factoid, comment_id= comment_id
                    ) 
        seen=set([])
        todo=set(stack.keys())
        last_seen = -1 
        while len(seen) != last_seen:
            last_seen = len(seen)
            todo2 = todo.copy()
            for id, comment in stack.items():
                for dest in todo:
                    if comment["comment_id"] == dest and dest != None:
                        if id not in seen:
                            transition += [( id, dest ),]
                            todo2 -= { dest, }
                            todo2 |= {id,}
                            seen |= {id,}
                    todo = todo2.copy()
        to_remove = set()
        log("trans", ln=line(), context=transition)
        for t in reversed(transition):
            _from, _to =t 
            if not "answer" in stack[_to]:
                stack[_to]["answer"] = []
            stack[_to]["answer"] +=  [ stack[_from], ]
            if _from != _to:
                to_remove |= {_from,}
        for id, comment in stack.items():
            if id not in to_remove:
                fo["result"] += [ comment, ]
    if route in { "comment", }:
        fo["annexe"]= mdict()

        with engine.connect() as cnx:
            from sqlalchemy import text 
            for s in cnx.execute(text(f"""select id, annexe_file from annexe """)):
                comment_id, annexe_file=s
                fo['annexe'] += mdict({comment_id: [annexe_file]})

# MAKO HANDLING
    
    potential_file = os.path.join("templates", route)
    if os.path.isfile(potential_file):
        start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
        env = TemplateLookup(directories=['./'])
        to_write = Template(filename=potential_file,lookup=env).render(
            fo= { k:v for k,v in fo.dict.items() if "secret" not in k}
        )
    else:
        start_response('200 OK', [('Content-type', 'application/json; charset=utf-8')])
        to_write = dumps({ k:v for k,v in fo.dict.items() if "secret" not in k}, indent=4, default=str)

    return [ to_write.encode() if hasattr(to_write, "encode") else to_write  ]


print("Crudest CRUD of them all on port 5000...")
make_server('', PORT, simple_app).serve_forever()
