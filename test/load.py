from requests import post
from html.parser import HTMLParser

import requests
import os
from dateutil import parser

# heaviweight
from requests import get
DB=os.environ.get('DB','test.db')
DB_DRIVER=os.environ.get('DB_DRIVER','sqlite')
ENDPOINT="http://127.0.0.1:5000"
os.chdir("..")
os.system(f"rm {DB}")
os.system("pkill -f scam.py ; sleep 2")
from time import sleep
sleep(2)
os.system(f"DB={DB} DB_DRIVER={DB_DRIVER} python scam.py & sleep 2")
url = lambda table : ENDPOINT + "/" + table
os.system(f"curl {url('group')}?_action=search")
# make sure db is bootstraped 

post(url("user"), params = dict(id=1,  secret_password="toto", name="jul2", email="j@j.com", _action="create"), files=dict(pic_file=open("./assets/favicon.ico", "rb").read())).status_code



#os.system(f"curl {ENDPOINT}/user?_action=search")
#os.system(f"sqlite3 {DB} .dump")

for table,values in tuple([
    ("user", dict( name="him", email="j2@j.com", secret_password="toto")),
    ("comment", dict(id=1,user_id=1, message="usable agile workflow", category="story" )),
    ("comment", dict(id=2,user_id=1,comment_id=1, message="How do we code?", category="story_item" )),
    ("comment", dict(id=3,user_id=1,comment_id=2,message="which database?", category="question")),
    ("comment", dict(id=4,user_id=2, comment_id=2,message="which web framework?",
    factoid = "https://github.com/jul/scam/blob/main/templates/model.mako", category="question")),
    ("comment", dict(id=5,user_id=2, comment_id=3, message="preferably less", category="answer")),
    ("transition", dict(id=5, previous_comment_id=4, next_comment_id=5)),
    ("transition", dict(id=7, previous_comment_id=2, next_comment_id=5)),

    ("comment", dict(id=6,comment_id=2,user_id=1, message="How do we test?", category="story_item" )),
    ("comment", dict(id=7,comment_id=6,user_id=2, message="QA framework here", category="delivery" )),
    ("comment", dict(id=8,comment_id=7,user_id=1, message="test plan", category="test" )),
    ("comment", dict(id=9,comment_id=8,user_id=1, message="OK", category="finish" )),
    ("comment", dict(id=10, comment_id=9, user_id=1, message="PoC delivered",category="delivery")),
    ]):

    values["_action"] = "create"
    post(url(table), params = values)
os.system("python ./generate_state_diagram.py sqlite:///test.db > out.dot ;dot -Tsvg out.dot > diag2.svg; firefox diag2.svg")

print(post(url("grant"), params = dict(secret_password="toto", email="j@j.com", )).status_code)
print(post(url("grant"), params = dict(_redirect="/users",secret_password="toto", email="j@j.com", )).status_code)
print(post(url("comment"), params=dict(_action="search", )).text)
os.system("pkill -f scam.py")
