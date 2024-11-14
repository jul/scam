from requests import post
import os
# heaviweight
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
DB=os.environ.get('DB','test.db')
DB_DRIVER=os.environ.get('DB_DRIVER','sqlite')
DSN=f"{DB_DRIVER}://{DB_DRIVER == 'sqlite' and not DB.startswith('/') and '/' or ''}{DB}"
ENDPOINT="http://127.0.0.1:5000"
os.system(f"rm {DB}")
os.system(f"DB={DB} DB_DRIVER={DB_DRIVER} python ../pdca.py & sleep 5")
# make sure db is bootstraped 


url = lambda table : ENDPOINT + "/" + table
post(url("user"), params = dict(id=1,  secret_password="aucun", name="jul2", email="j2@j.com", _action="create"), files=dict(pic_file=open("diag.png", "rb").read())).text
os.system(f"curl {ENDPOINT}/user?_action=search")
os.system(f"sqlite3 {DB} .dump")
os.system("pkill -f ../pdca.py")
engine = create_engine(DSN)
metadata = MetaData()
metadata.reflect(bind=engine)
Base = automap_base(metadata=metadata)
Base.prepare()
with Session(engine) as session:
    for table,values in tuple([
        ("group", dict(id=1, name="trolol") ),
        ("group", dict(id=2, name="serious") ),
        ("user_group", dict(id=1,user_id=1, group_id=1, secret_token="secret")),
        ("statement", dict(id=1,user_group_id=1, message="usable agile workflow", category="story" )),
        ("statement", dict(id=2,user_group_id=1, message="How do we code?", category="story_item" )),
        ("statement", dict(id=3,user_group_id=1, message="which database?", category="question")),
        ("statement", dict(id=4,user_group_id=1, message="which web framework?", category="question")),
        ("statement", dict(id=5,user_group_id=1, message="preferably less", category="answer")),
        ("statement", dict(id=6,user_group_id=1, message="How do we test?", category="story_item" )),
        ("statement", dict(id=7,user_group_id=1, message="QA framework here", category="delivery" )),
        ("statement", dict(id=8,user_group_id=1, message="test plan", category="test" )),
        ("statement", dict(id=9,user_group_id=1, message="OK", category="finish" )),
        ("statement", dict(id=10, user_group_id=1, message="PoC delivered",category="delivery")),

        ("transition", dict( user_group_id=1, previous_statement_id=1, next_statement_id=2, message="something bugs me",is_exception=True, )),
        ("transition", dict( 
            user_group_id=1, 
            previous_statement_id=2, 
            next_statement_id=4, 
            message="standup meeting feedback",is_exception=True, )),
        ("transition", dict( 
            user_group_id=1, 
            previous_statement_id=2, 
            next_statement_id=3, 
            message="standup meeting feedback",is_exception=True, )),
        ("transition", dict( user_group_id=1, previous_statement_id=2, next_statement_id=6, message="change accepted",is_exception=True, )),
        ("transition", dict( user_group_id=1, previous_statement_id=4, next_statement_id=5, message="arbitration",is_exception=True, )),
        ("transition", dict( user_group_id=1, previous_statement_id=3, next_statement_id=5, message="arbitration",is_exception=True, )),
        ("transition", dict( user_group_id=1, previous_statement_id=6, next_statement_id=7, message="R&D", )),
        ("transition", dict( user_group_id=1, previous_statement_id=7, next_statement_id=8, message="Q&A", )),
        ("transition", dict( user_group_id=1, previous_statement_id=8, next_statement_id=9, message="CI action", )),
        ("transition", dict( user_group_id=1, previous_statement_id=2, next_statement_id=10, message="situation unblocked", )),
        ("transition", dict( user_group_id=1, previous_statement_id=9, next_statement_id=10, message="situation unblocked", )),
        ]):
        session.add(getattr(Base.classes,table)(**values))
        session.commit()
#n        os.system(f"curl {url(table)}?_action=search")
os.system("python ../generate_state_diagram.py sqlite:///test.db > out.dot ; xdot out.dot")
