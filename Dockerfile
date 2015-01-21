FROM dockerfile/ubuntu
MAINTAINER binux <roy@binux.me>

# install python
RUN apt-get update && \
    apt-get install -y python python-dev python-distribute python-pip && \
    apt-get install -y libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml libffi-dev

# install requirements
ADD requirements.txt /opt/pyspider/requirements.txt
RUN pip install --allow-all-external -r /opt/pyspider/requirements.txt

# add all repo
ADD ./ /opt/pyspider
WORKDIR /opt/pyspider

RUN pip install .

VOLUME ["/opt/pyspider"]

EXPOSE 5000 23333 24444

RUN groupadd -r pyspider && useradd -r -g pyspider -d /opt/pyspider \
    -s /sbin/nologin pyspider
RUN chown -R pyspider:pyspider /opt/pyspider

USER pyspider
ENTRYPOINT ["pyspider"]
