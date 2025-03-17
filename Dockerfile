FROM debian
ARG DB
ENV DB $DB
ENV LANG C.UTF-8
RUN mkdir -p /scam/assets
RUN mkdir -p /usr/share/man/man1 && mkdir -p /usr/share/man/man7
RUN apt-get update && apt-get -y dist-upgrade \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get -y --no-install-recommends install \
	python3 python3-pip python3-venv python3-setuptools \
    python3-sqlalchemy texlive pandoc graphviz virtualenv \
    python3-magic sqlite3 texlive-xetex texlive-latex-extra \
    texlive-fonts-recommended texlive-lang-french graphviz lmodern 

RUN sed -i 's/^Components: main$/& contrib/' \
        /etc/apt/sources.list.d/debian.sources
RUN apt-get update
RUN apt-get install -y ttf-mscorefonts-installer fontconfig
RUN fc-cache -f -v

RUN useradd scam -d /scam --uid 1000 -m -s /bin/bash
RUN mkdir /venv
RUN virtualenv --system-site-packages /venv
COPY --chown=scam . /scam
WORKDIR /scam
RUN . /venv/bin/activate
ENV PYTHONPATH=/venv/bin
RUN /venv/bin/python -m pip install --no-cache-dir \
    --disable-pip-version-check -r /scam/requirements.full.txt
USER scam
EXPOSE 5000
CMD . /venv/bin/activate && cd /scam \
    && DB=${DB:-scam} /venv/bin/python /scam/scam.py
