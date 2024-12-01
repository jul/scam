from requests import post
from html.parser import HTMLParser

import requests
import os
from dateutil import parser
from passlib.hash import scrypt as crypto_hash # we can change the hash easily
from urllib.parse import parse_qsl, urlparse

# heaviweight
from requests import get
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
DB=os.environ.get('DB','test.db')
DB_DRIVER=os.environ.get('DB_DRIVER','sqlite')
DSN=f"{DB_DRIVER}://{DB_DRIVER == 'sqlite' and not DB.startswith('/') and '/' or ''}{DB}"
ENDPOINT="http://127.0.0.1:5000"
os.chdir("..")
os.system(f"rm {DB}")
os.system(f"DB={DB} DB_DRIVER={DB_DRIVER} python pdca.py & sleep 2")
url = lambda table : ENDPOINT + "/" + table
os.system(f"curl {url('group')}?_action=search")
# make sure db is bootstraped 





form_to_db = transtype_input = lambda attrs : {  k: (
                # handling of input having date/time in the name
                "date" in k or "time" in k and v and type(k) == str )
                    and parser.parse(v) or
                # handling of boolean mapping which input begins with "is_"
                k.startswith("is_") and [False, True][v == "on"] or
                # password ?
                "password" in k and crypto_hash.hash(v) or
                v
                for k,v in attrs.items() if v  and not k.startswith("_")
}

post(url("user"), params = dict(id=1,  secret_password="toto", name="jul2", email="j@j.com", _action="create"), files=dict(pic_file=open("./assets/diag.png", "rb").read())).status_code
#os.system(f"curl {ENDPOINT}/user?_action=search")
#os.system(f"sqlite3 {DB} .dump")

engine = create_engine(DSN)
metadata = MetaData()


transtype_true = lambda p : (p[0],[False,True][p[1]=="true"])
def dispatch(p):
    return dict(
        nullable=transtype_true,
        unique=transtype_true,
        default=lambda p:("server_default",eval(p[1])),
    ).get(p[0], lambda *a:None)(p)

transtype_input = lambda attrs : dict(filter(lambda x :x, map(dispatch, attrs.items())))

class HTMLtoData(HTMLParser):
    def __init__(self):
        global engine, tables, metadata
        self.cols = []
        self.table = ""
        self.tables= []
        self.enum =[]
        self.engine= engine
        self.meta = metadata
        super().__init__()

    def handle_starttag(self, tag, attrs):
        global tables
        attrs = dict(attrs)
        simple_mapping = {
            "email" : UnicodeText, "url" : UnicodeText, "phone" : UnicodeText,
            "text" : UnicodeText, "checkbox" : Boolean, "date" : Date, "time" : Time,
            "datetime-local" : DateTime, "file" : Text, "password" : Text, "uuid" : Text, #UUID is postgres specific
        }

        if tag in {"select", "textarea"}:
            self.enum=[]
            self.current_col = attrs["name"]
            self.attrs= attrs
        if tag == "option":
            self.enum.append( attrs["value"] )
        if tag == "unique_constraint":
            self.cols.append( UniqueConstraint(*attrs["col"].split(','), name=attrs["name"]) )
        if tag in { "input" }:
            if attrs.get("name") == "id":
                self.cols.append( Column('id', Integer,  **( dict(primary_key = True) | transtype_input(attrs ))))
                return
            try:
                if attrs.get("name").endswith("_id"):
                    table=attrs.get("name").split("_")
                    self.cols.append( Column(attrs["name"], Integer, ForeignKey(attrs["reference"])) )
                    return
            except Exception as e:
                log(e, ln=line())

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
        global tables
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
            #tables[self.table] = self.tables[-1]

            self.cols = []
            with engine.connect() as cnx:
                self.meta.create_all(engine)
                cnx.commit()

HTMLtoData().feed(get("http://127.0.0.1:5000/").text)
os.system("pkill -f pdca.py")



#metadata.reflect(bind=engine)
Base = automap_base(metadata=metadata)

Base.prepare()

with Session(engine) as session:
    for table,values in tuple([
        ("user", form_to_db(dict( name="him", email="j2@j.com", secret_password="toto"))),
        ("comment", dict(id=1,user_id=1, message="usable agile workflow", category="story" )),
        ("comment", dict(id=2,user_id=1,comment_id=1, message="How do we code?", category="story_item" )),
        ("comment", dict(id=3,user_id=1,comment_id=2,message="which database?", category="question")),
        ("comment", dict(id=4,user_id=2, comment_id=2,message="which web framework?", category="question")),
        ("comment", dict(id=5,user_id=2, comment_id=3, message="preferably less", category="answer")),
        ("transition", dict(id=5, previous_comment_id=4, next_comment_id=5)),
        ("transition", dict(id=7, previous_comment_id=2, next_comment_id=5)),

        ("comment", dict(id=6,comment_id=2,user_id=1, message="How do we test?", category="story_item" )),
        ("comment", dict(id=7,comment_id=6,user_id=2, message="QA framework here", category="delivery" )),
        ("comment", dict(id=8,comment_id=7,user_id=1, message="test plan", category="test" )),
        ("comment", dict(id=9,comment_id=8,user_id=1, message="OK", category="finish" )),
        ("comment", dict(id=10, comment_id=9, user_id=1, message="PoC delivered",category="delivery")),
        ]):

        session.add(getattr(Base.classes,table)(**values))
        #getattr(Base.classes,table)(**values)
        session.commit()
os.system("python ./generate_state_diagram.py sqlite:///test.db > out.dot ;dot -Tpng out.dot > diag2.png; xdot out.dot")
s = requests.session()

os.system(f"DB={DB} DB_DRIVER={DB_DRIVER} python pdca.py & sleep 1")


print(s.post(url("grant"), params = dict(secret_password="toto", email="j@j.com",group_id=1, )).status_code)
print(s.post(url("grant"), params = dict(_redirect="/group",secret_password="toto", email="j@j.com",group_id=2, )).status_code)
print(s.cookies["Token"])
print(s.post(url("comment"), params=dict(_action="search", )).text)
os.system("pkill -f pdca.py")
