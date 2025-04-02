FROM docker.elastic.co/elasticsearch/elasticsearch:8.14.3


ENV discovery.type=single-node
ENV xpack.security.enabled=false


COPY --chown=elasticsearch:elasticsearch data/ /usr/share/elasticsearch/data


RUN chmod -R 0775 /usr/share/elasticsearch/data


RUN find /usr/share/elasticsearch/data -type f -name "*.lock" -delete
RUN rm -f /usr/share/elasticsearch/data/nodes/0/node.lock
