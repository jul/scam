% SCAM Manual
% jul 
% $Version: 202503$ \
  \ 
  \ ![](aide.annexe.1){width=7cm}
---
fontsize: 10pts
documentclass: extreport
papersize: a4 
header-includes:
 - \usepackage{hyperref}
 - \definecolor{myblue}{rgb}{0.28, 0.24, 0.48}
 - \hypersetup{colorlinks=true, allcolors=myblue} 
---

WTFPL 2.0 Do any thing you want with this book except claim you wrote it

# Synopsis

> To look smart you either say it in latin or write in LaTeX and add the
> Naviers Stocke equation
> $$\frac{\partial \rho}{\partial t} + \vec{\nabla} \cdot \vec{j} = 0$$
> to look smarter

But most of us ain't smart enough to use LaTeX, at most we can use
markdown an easy to learn text renderer.

So here is my solution to be a professional scamer : this is a front end
to a pandoc toolchain based on mind mapping for structuring the thoughts
with a real time rendering of the markdown and quite a few tricks.

![screenshot of the markdown editing ot this
page](aide.annexe.2){width="16cm"}

[The home page of SCAM is on github](http://github.com/jul/scam)

```{=tex}
\newpage
```
# Installation

I am too lazy to write an install script, make a debian package, or a
full pip requirements solution because I need binary installs.

As a result I resorted to the solution of the lazy man which source
tells you all you need : making it a docker file.

``` dockerfile
FROM debian
ENV LANG C.UTF-8
RUN mkdir -p /usr/share/man/man1 && mkdir -p /usr/share/man/man7
RUN apt-get update && apt-get -y dist-upgrade \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get -y --no-install-recommends install \
	python3 python3-pip python3-venv python3-setuptools \
    python3-sqlalchemy texlive pandoc graphviz virtualenv \
    python3-magic sqlite3 texlive-xetex texlive-latex-extra \
    texlive-fonts-recommended texlive-lang-french lmodern

RUN useradd scam -d /app --uid 1000 -m -s /bin/bash
COPY --chown=scam . /app
WORKDIR /scam
RUN mkdir /scam/assets /venv
RUN chown -R scam:scam .
COPY  . .
RUN virtualenv --system-site-packages /venv
RUN . /venv/bin/activate
COPY requirements.full.txt .
ENV PYTHONPATH=/venv/bin
RUN /venv/bin/python -m pip install --no-cache-dir \
    --disable-pip-version-check -r requirements.full.txt
EXPOSE 5000
USER scam
CMD . /venv/bin/activate && cd /scam && DB=${db:-scam} /venv/bin/python /app/scam.py
```

with the following requirements :

    archery
    pandoc-include
    dateutils
    multipart
    filelock
    Mako
    pandocfilters
    panflute
    passlib
    python-dateutil
    SQLAlchemy>=2
    SQLAlchemy-Utils
    time-uuid

to use it I recommend the side car technique wich can be used this way
so that you can access the assets dir which contain the book :

    docker build -t scam . 
    docker run -i -t -e db=bookname \
        --mount type=bind,src=.,dst=/scam \
        -p5000:5000  scam 
    firefox http://127.0.0.1:5000

```{=tex}
\newpage
```
# Walkthrough: writing the aide

## Creating your first post

[The landing page](http://127.0.0.1:5000/) give you one option : POST :D

![Graph interface : time to create your first post](aide.annexe.4)

```{=tex}
\newpage
```
On click you should see this and be able to fill the value:

![First post](aide.annexe.6)

and then click *create*

```{=tex}
\newpage
```
## Attaching a content to an entry.

I chose the policy that one micro item is related to one and only one
attachment of the embedable kind you want.

The **annexe** widget below is used to load and delete annexes (attached
files) that will be stored in the database.

These items will be available as pictures in the markdown editor by the
given name on the top.

![by clicking on the « attach » button you can attach a content to the
post it entry](aide.annexe.9)

## Accessing the text

To access the post entry you click on the node/post and it will open a
modal window in which the **text** button is accessible for editing your
book text

![Once you click on a node in the graph the post editing interface
appear](aide.annexe.13)

## Developping your first comment and setting your book title

First comment is specific in the sense it is also used for the title.
With pandoc you can add metada used for LaTeX.

The [*markdown* extension useds here is the pandoc
one](https://pandoc.org/MANUAL.html#pandocs-markdown)

Here is a typical Pandoc flavoured Markdown entry to setup the LaTeX
settings here with the french settings :

    % TITLE
    % AUTHOR
    % DATE \
      \ 
      \ ![](aide.annexe.1){width=15cm}

    ---
    header-includes:
     - \usepackage[french]{babel}
     - \usepackage{hyperref}
     - \definecolor{myblue}{rgb}{0.28, 0.24, 0.48}
     - \hypersetup{colorlinks=true, allcolors=myblue} 
     - \let\tmp\oddsidemargin
     - \let\oddsidemargin\evensidemargin
     - \let\evensidemargin\tmp
      - \reversemarginpar
     ---

Your real time markdown input is definitely confused but that's fine. It
is a quirk :D

![screenshot of the rendered PDF with the title](aide.annexe.10)

# Visualizing your document

Now that you have rinced and repeated a few time the post entry/text
process you may want to check the output.

There are 2 main output : HTML and PDF.

## HTML output

To see the result

[it's now time to visit the HTML rendering
URL](http://127.0.0.1:5000/book). You should have a side by side view of
the generated standalone HTML and the generated PDF.

![book rendering](aide.annexe.11)

You notice that there is a nice self embedded HTML link. This includes
CSS and pictures inside the document for serving the document as a
single file.

```{=tex}
\newpage
```
## PDF

The [PDF renderer](http://127.0.0.1:500/pdf) accessible from the menu
will give you the PDF rendering.

![PDF view of the document](aide.annexe.14)

# Rinse and repeat

Ather a few more entries that are boring because very repitive if [you
consult the graph URL](http://127.0.0.1:5000/svg) you should have now
more entries.

![Your graph should now expand itself as the book](aide.annexe.12)

The « book order » is the red lines, they follow the ascending id order
but can be overriden with the book_order rank available in the **text**
view.

# Playing with the help example

This book is available in the repository as a sqlite database.

To try it :

     docker run -i -t -e db=aide --mount type=bind,src=.,dst=/scam \
         -p5000:5000 --user  1000:1000  scam
     firefox http://127.0.0.1:5000

# Dev corner

## « Design »

Well, there was no design.

All I know is that web services came first and that all User Interface
is based on calling them in ajax.

[Web services](http://127.0.0.1:5000/model) are presented as a serie of
form, one for each table, and the actions required to be filled in the
request are the *input type=submit* button.

![Exemple of a REST access to the table comment](aide.annexe.15)

You can check how it is done in [the lite suite I use to test part of
the design](https://github.com/jul/scam/blob/main/test/load.py).

## Synchronous

Since all my *events* meaningful (saving) are plugged on *onclick*
events in javascript, it is a synchronous application ensuring that when
my wife and kid interrupt me, the document is always in a sane state. So
far, I love it so much because it actually acted as a safeguard in the
here fore mentioned situations in real life during the writing of this
manual, that I am reluctant to put an « autosave » feature.

But, nice to have would be a « CTRL+S » binding that does the save with
a nice modal message.

**CAVEAT** : hit update often or you shall lose work.

## Model

A careful examination of the entity relationship diagram will point at
**dead** data such as the user table, or the factoid column that is not
used anymore.

![Entity Relationship Diagram](aide.annexe.16)

As you can notice the **comment** table is the center of the model.

## Creativity boosters (limitations)

Pretty much these limitations are due to some of my lack of skills.

You have the following important limitations :

-   there is a one to one association between *annexe* (joint picture)
    and a *comment*[^1] ;

```{=html}
<!-- -->
```
-   there is a one to one association between *annexe* (joint picture)
    and a (markdown) *text* and the joint is on .... *comment_id* or
    *id*[^2] ;

-   the table **transition** adds an edge between comments on the
    graph[^3]

```{=html}
<!-- -->
```
-   the *factoid* column of the **comment** table is not used anymore
    [^4];
-   the **user** table is not used anymore [^5];

# Serendipity

Also called « un planned features ».

## Vanilla Markdown export with assets (gruik inside)

You noticed there on the [page for the html
export](http://127.0.0.1:5000/book) that there is a link for the full
markdown export.

Actually, it is a modified markdown with with some [custom pandoc
processing](https://github.com/jul/scam/blob/main/mkdoc.sh) with pandoc
lua filters applied and a tad of pandoc magic.

So you will need this file to make your own builder, and also the images
that are automatically generated upon calling the HTML view[^6]. The
picture needed to complete the markdown export will be located in the
assets directory with the name `assets/$DB.annexe.*` where DB is the
name of the DB you use (default is **scam**).

## Self embedded HTML

I am testing single HTML self containing page with the pictures embedded
inside.

Test it for me, and if it works it will become the default and only HTML
view.

# Psycodelic experience

Most the making of this software *-due to an intense real life pain-*
have been made under drugs such as ketoprofen, opium and more.

Pain and drugs totally change the way you code, if you want to go on
foreward, you have to sharpen your mind through the pain to stay
focused, ensuring a maximal brutality to hack your way.

As the maintainer of the source code I have been pleasantly surprised by
how easy it was for me to understand what I did, even though it totally
goes against the currently admitted best practices of full stack
development (such as using fucking frameworks for every layers of the
stack).

It is like discovering your true self in coding because you had to code
so diminished intellectually that it prevented your past self to be too
smart for your present self with more brain.

Since I don't like pain, it is an experience I don't recommend.

[^1]: because I did not wanted to code a file explorer of the potential
    attachment (I hate front end development as much as back end one);

[^2]: I did messed up thing if I remember well, and I'm pretty sure that
    instead of a joint on *comment_id* I do it in one tiny **vicious**
    place of the interface on *id*.

[^3]: I am beginning to find this feature useless. Less is more, hence
    I'm thinking of removing it.

[^4]: I changed the interface by removing features, but I had the
    lazyness to write the migration script and change the custom SQL I
    wrote. Planning for migration scripts and version handling is quite
    a lot of work you know, that I will not priorize because, I have the
    skills, but not the will.

[^5]: same thing as above

[^6]: I think I forgot to check if images were present before generating
    the PDF assuming people would check the HTML first. Stupid me.
