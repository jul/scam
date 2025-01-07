#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from textwrap import wrap , shorten 
from html import escape 

from sys import argv

print( """digraph structs {
          fontname="Courier New"
    graph [
       rankdir= "TB"
       bgcolor = "#f5f5ff"
    ]

    overlapse=false
    
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
cat_colors= dict()
cat_bg_colors=dict(
    end="#a0a0f0",
    comment="#ffffff",
    answer="#f0f0e0",
    story="#f0c0d0",
    story_item="#ffe0f0",
    question="#e0f0f0",
    test="#ffe0d0",
    delivery="#c0f0d0",
    finish="#d0d0d0",
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
        new_message = message.split("\n")
        new_message = list(map(lambda s:wrap(escape(s).replace("\n", "\\l")), new_message))
        new_message = "\\l".join(list(map("\\l".join, new_message)))
        if factoid != None:
            new_message += "\\l" + f"""{factoid}"""

        print(f"""{id} [label="{id}:{category}:@{user_id}\\n{new_message}\\l" fillcolor="{cat_bg_colors.get(category,"gray")}" color="{cat_colors.get(category, "gray")}"];""")
        


    fake_id=1
    for s in sql.execute(text("""select t.previous_comment_id, t.next_comment_id from transition t, comment c, comment c2 where t.next_comment_id = c.id and t.previous_comment_id=c2.id and t.previous_comment_id not in ( 
with recursive is_fin(b) as
                (
                    select comment_id from comment
                        where category="finish"
                    UNION
                    select comment_id
                    from comment JOIN  is_fin
                    ON comment.id=is_fin.b 
               ) SELECT id FROM comment where id in is_fin


        ) and t.next_comment_id not in (
            with recursive is_fin(b) as
                (
                    select comment_id from comment
                        where category="finish"
                    UNION
                    select comment_id
                    from comment JOIN  is_fin
                    ON comment.id=is_fin.b
               ) SELECT id FROM comment where id in is_fin
            )
        ;""")):

        previous_comment_id, next_comment_id = s
        print(f"""{previous_comment_id} -> {next_comment_id} ;""")
    print("comment=this")
    for s in sql.execute(text("""select c1.comment_id, c1.id from comment as c1 INNER JOIN comment as c2 ON c1.comment_id = c2.id WHERE  c1.category != "finish" and c1.id NOT IN (
            with recursive is_fin(b) as
                (
                    select comment_id from comment
                        where category="finish"
                    UNION
                    select comment_id
                    from comment JOIN  is_fin 
                    ON comment.id=is_fin.b 
               ) SELECT id FROM comment where id in is_fin) ;""")):
        comment_id, id = s
        if None not in { comment_id, id }:
            
            print(f"""{comment_id} -> {id};""")

print("}")
