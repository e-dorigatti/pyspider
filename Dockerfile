FROM cmfatih/phantomjs
MAINTAINER binux <roy@binux.me>

# install python
RUN apt-get update && \
    apt-get install -y python python-dev python-distribute python-pip pdftohtml && \
    apt-get install -y libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml && \
    apt-get install -y libffi-dev libpq-dev wget

# install requirements
ADD requirements.txt /opt/pyspider/requirements.txt
RUN pip install -r /opt/pyspider/requirements.txt
RUN pip install -U pip

RUN wget http://ftp.jaist.ac.jp/pub/mysql/Downloads/Connector-Python/mysql-connector-python-2.1.3.tar.gz
RUN tar zxvf mysql-connector-python-2.1.3.tar.gz
RUN cd mysql-connector-python-2.1.3 && python setup.py install

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider

RUN pip install .
RUN pip install -e .[all]

VOLUME ["/opt/pyspider"]
ENTRYPOINT ["pyspider"]

EXPOSE 5000 23333 24444 25555

RUN groupadd -r pyspider && useradd -r -g pyspider -d /opt/pyspider \
    -s /sbin/nologin pyspider
RUN chown -R pyspider:pyspider /opt/pyspider

USER pyspider
ENTRYPOINT ["pyspider"]
