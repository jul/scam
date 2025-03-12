#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import *
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

from sys import argv

DIGRAPH = """digraph structs {
    graph [
       rankdir= "LR"
       bgcolor=white
    ]
    
    node [ 
        fontsize=12
        fontname="Courier New"
        shape=record 
    ]
    
    %s
}
"""

db=create_engine(argv[1])

print( "introspecting %s" %  argv[1])
metadata = MetaData()
metadata.reflect(bind=db)

Base = automap_base(metadata=metadata)
Base.prepare()
to_scan = list(metadata.tables.keys())
vertices = []
nodes = dict()
interesting = set([])
fk_count = 0
field_count = 0

while to_scan:
    node_str = ''
    try:
        table_name = to_scan.pop()
        table = metadata.tables[table_name]
        node_str += """
    %s [ 
        label="Table: %s\\l""" % (table_name, table_name,)
        has_fk=False
        for c in table.c:
            node_str += "|<%s>- %s\\l" % (c.name, c.name)
            field_count += 1
            #print "adding %s" % c.name
            if c.foreign_keys:
                for fk in c.foreign_keys:
                    interesting |= { table_name, fk.column.table.name, }
                    fk_count+=1
                    # if you want to make a progressive scan around a table vicinity
                    #to_scan += [ fk.column.table.name ]
                    vertices += [ (
                        ":".join([table_name, c.name]),  
                        ":".join([ fk.column.table.name, fk.column.name]),
                        fk.name or '""'),
                    ]
                    
        nodes[table_name] = """%s"
        color=%%s
        bgcolor=%%s
    ]""" % node_str
            
    except Exception as e:
        print( "problem with %r" % table_name)
        print( repr(e) )
        

to_print = ""
for node in nodes:
    #to_print += node % (("grey","grey"), ("black", "white"))[node in interesting]
    to_print += nodes[node] % (("grey","grey"), ("black", "white"))[node in interesting]

    
for v in vertices:
    to_print+="""
    %s -> %s [ label=%s ]
""" % v
to_print = DIGRAPH % to_print 
print( "nb col = %r" % field_count )
print( "nb fk = %r" % fk_count )

with open("out.dot", "w") as f: f.write(to_print)
