#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from sys import argv

print( """digraph structs {
    graph [
       rankdir= "LR"
       bgcolor=white
    ]
    
    node [ 
        fontsize=12 
        shape=record 
    ]
""")

db=create_engine(argv[1])

cat_colors=dict(
    plan="red",
    do="blue",
    check="green",
    correct="yellow",
    end="black",
    story="red",
    story_item="brown",
    question="blue",
    answer="yellow",
    test="orange",
    finish="black",
    delivery="green",
)
seen = dict()
with db.connect() as sql:
    for s in sql.execute(text("select id, message, factoid, category from comment")):
        id, message, factoid, category= s
        print(f"""{id} [label="{id}|{category}|{message}|{factoid}" color="{cat_colors.get(category, "gray")}"];""")
    fake_id=1
    for s in sql.execute(text("select previous_comment_id, next_comment_id from transition;")):
        previous_comment_id, next_comment_id = s
        print(f"""{previous_comment_id} -> {next_comment_id};""")
    for s in sql.execute(text("select comment_id, id from comment;")):
        comment_id, id = s
        print(f"""{comment_id} -> {id};""")

print("}")
