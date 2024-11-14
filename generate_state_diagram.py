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

with db.connect() as sql:
    for s in sql.execute(text("select id, message, factoid, category from statement")):
        id, message, factoid, category= s
        print(f"""{id} [label="{id}|{category}|{message}|{factoid}" color="{cat_colors.get(category, "gray")}"];""")
    fake_id=1
    for s in sql.execute(text("select id, message, factoid, previous_statement_id, next_statement_id from transition")):
        id, message, factoid, previous_statement_id, next_statement_id = s
        if not next_statement_id:
            next_statement_id = "unk_%d" % fake_id
            fake_id+=1
            print(f"""{next_statement_id} [label="unknown|sid|None" color="grey"];  """)
        print(f"""{previous_statement_id} -> {next_statement_id} [label="{id}|{message}" ];""")
print("}")
