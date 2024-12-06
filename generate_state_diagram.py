#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from textwrap import wrap , shorten 
from urllib.parse import quote

from sys import argv

print( """digraph structs {
    graph [
       rankdir= "TB"
    ]
    
    node [ 
        fontsize=12 
        style="rounded,filled"
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
cat_bg_colors=dict(
    end="black",
    story="#f0b0c0",
    story_item="#d0b080",
    question="#c0e0f0",
    answer="#f0f0c0",
    test="#f0c060",
    finish="#d0d0d0",
    delivery="#c0f0d0",
)
seen = dict()
with db.connect() as sql:
    for s in sql.execute(text("""
        select id,user_id, message, factoid, category
        from comment
         WHERE  comment.category != "finish" and comment.id NOT IN (
            with recursive is_fin(b) as
                (
                    select comment_id from comment
                        where category="finish"
                    UNION
                    select comment_id
                    from comment JOIN  is_fin
                    ON comment.id=is_fin.b
               ) SELECT id FROM comment where id in is_fin ) ;""")):
        id, user_id,message, factoid, category= s
        print(f'''{id} [label="{id}:{category}:@{user_id}\\n{"\\l".join(wrap(message.replace("\n","\\l"),30))}" fillcolor="{cat_bg_colors.get(category,"gray")}" color="{cat_colors.get(category, "gray")}"];''')
        


    fake_id=1
    for s in sql.execute(text("""select previous_comment_id, next_comment_id from transition JOIN comment ON comment.id = transition.next_comment_id and comment.id = transition.previous_comment_id ;""")):
        previous_comment_id, next_comment_id = s
        print(f"""{previous_comment_id} -> {next_comment_id};""")
    for s in sql.execute(text("""select comment_id, id from comment WHERE  comment.category != "finish" and comment.id NOT IN (
            with recursive is_fin(b) as
                (
                    select comment_id from comment
                        where category="finish"
                    UNION
                    select comment_id
                    from comment JOIN  is_fin 
                    ON comment.id=is_fin.b where comment.category != "story"
               ) SELECT id FROM comment where id in is_fin) ;""")):
        comment_id, id = s
        if None not in { comment_id, id }:
            
            print(f"""{comment_id} -> {id};""")

print("}")
