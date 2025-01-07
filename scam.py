#!/usr/bin/env python
# STDLIB 
import multipart
from wsgiref.simple_server import make_server
from json import dumps, loads
from html.parser import HTMLParser
from base64 import b64encode, b64decode
from urllib.parse import parse_qsl, urlparse
import traceback
from  http.cookies import SimpleCookie as Cookie
from uuid import UUID as  UUIDM # conflict with sqlachemy
from datetime import datetime as dt, UTC, timezone
import sys
from zlib import adler32
import os
# external dependencies
# lightweight
from archery import mdict
from dateutil import parser
from time_uuid import TimeUUID
# NEEDS A BINARY INSTALL (scrypt)
from passlib.hash import scrypt as crypto_hash # we can change the hash easily
# heaviweight
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database
from mako.template import Template
from mako.lookup import TemplateLookup



__DIR__= os.path.dirname(os.path.abspath(__file__))
DB=os.environ.get('DB','scam.db')
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
    try:
        fo["_secret_token"] = Cookie(environ["HTTP_COOKIE"])["Token"].value
    except:
        log("no cookie found", ln=line())
        
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
        print(dest)

    potential_file = os.path.join(__DIR__, "assets", route )
    if os.path.isfile(potential_file ):
## python-magic
        import magic
        start_response('200 OK', [('content-type',
            potential_file.endswith(".css") and "text/css"
            or magic.from_file(potential_file, mime=True)), ])
        log(magic.from_file(potential_file, mime=True), ln=line())
        return [ open(potential_file, "rb").read() ]


    form_to_db = lambda attrs : {  k: (
                    # handling of input having date/time in the name
                    "date" in k or "time" in k and v and type(k) == str )
                        and parser.parse(v) or
                    # handling of input type = form havin "file" in the name of the inpur
                    "file" in k \
                        and open(f"""./assets/{DB}.{fo["id"]}""", "wb").write(b64decode(fo[k]["content"])) \
                        and f"""data:{fo[k]["content_type"]}; base64, {fo[k]["content"].decode()}""" or

                    # handling of boolean mapping which input begins with "is_"
                    k.startswith("is_") and [False, True][v == "on"] or
                    # password ?
                    "password" in k and crypto_hash.hash(v) or
                    v
                    for k,v in attrs.items() if v != "" and not k.startswith("_")
    }
    action = fo.get("_action", "")

    def validate(fo):
        with Session(engine) as session:
            User = Base.classes.user
            try:
                user = session.scalars(select(User).where(User.secret_token==fo["_secret_token"])).one()
                log("token emitted since " + str( dt.now(UTC) - dt.fromtimestamp(TimeUUID(bytes=UUIDM("{%s}" % fo["_secret_token"]).bytes).get_timestamp(), UTC)), ln=line(),)
                fo["_user_id"]=user.id
                fo["_user_pic"]=user.pic_file
                all_user = session.execute(select(User)).scalars().all()
                fo["_pics"] = dict(map(lambda user:(user.id,user.pic_file),all_user))
                fo["_name"] = dict(map(lambda user:(user.id,user.name),all_user))

                return False
            except Exception as e:
                log(traceback.format_exc(), ln=line())
                start_response('302 Found', [('Location',f"""/login?_redirect={fo.get("_redirect",here)}""")], )


                return [ f"""<html><head><meta http-equiv="refresh" content="0; url="/login?_redirect=/</head></html>""".encode() ]

    if route=="grant":
        try:
            with Session(engine) as session:
                User = Base.classes.user
                user = session.scalars(select(User).where(User.email==fo["email"])).one()
                user.secret_token = str(TimeUUID.with_utcnow())
                fo["validate"] = crypto_hash.verify(fo["secret_password"], user.secret_password)
                session.flush()
                session.commit()
                if fo["validate"]:
                    # /!\ CRSF HERE /!\ unsecure 
                    start_response('302 Found', [('Location',f"""{fo.get("_redirect","/")}"""),('Set-Cookie', "Token=%s" % user.secret_token)], )
                    return [ f"""<html><head><meta http-equiv="refresh" content="0; url="{fo.get("_redirect","/")}")</head></html>""".encode() ]
                else:
                    raise Exception("Invalid token")
        except Exception as e:
            log("Auth failed for email " + fo["email"] , ln=line())
            start_response('403 wrong auth', [('Location',"/"), ])
            return [ "page denied".encode() ]



    if "_action" in fo and route in tables.keys():
        with Session(engine) as session:
            try:
                Item = getattr(Base.classes, table)
                if action == "delete":
                    #from pdb import set_trace; set_trace()
                    if fail := validate(fo):
                        return fail
                    
                    session.delete(session.get(Item, fo["id"]))

                    session.commit()
                    fo["result"] = "deleted"
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
                    if table == "user":
                        return redirect("/user_view?id=%s" % new_item.id)

                if action == "update":
                    if fail:= validate(fo):
                        return fail
                    item = session.scalars(select(Item).where(Item.id==fo["id"])).one()
                    for k,v in form_to_db(fo).items():
                        setattr(item,k,v)
                    session.commit()
                    fo["result"] = item.id
                    if table == "user":
                        return redirect("/user_view?id=%s" % item.id)
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
        route="index"
    to_write=""
    if route == "doc":
        if fail := validate(fo):
            return fail

        from subprocess import run, PIPE
        from urllib.parse import unquote
        run([ "pandoc", "-" , "--standalone", "-s", "-c" ,"pandoc.css","--metadata", "title=",  "-o" ,f"""./assets/{fo["id"]}.html""" ], input=unquote(fo.get("text","")).encode(), stdout=PIPE)
        start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])
        return [ open(f"""./assets/{fo["id"]}.html""", "rt").read().encode() ]
    

    if route == "svg":
        if fail := validate(fo):
            return fail
            
        from filelock import FileLock
        with FileLock('out.dot.lock'):
            os.system(f"python ./generate_state_diagram.py {DSN} > out.dot ;dot -Tsvg out.dot > diag2.svg; ")
    
    if route == "comment":
        if fail := validate(fo):
            return fail
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
                    """,id=id)):
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
    if route in { "comment", "svg"}:
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
make_server('', 5000, simple_app).serve_forever()
