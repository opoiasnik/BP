FROM docker.elastic.co/elasticsearch/elasticsearch:8.14.3

# Отключаем безопасность для упрощения доступа
ENV discovery.type=single-node
ENV xpack.security.enabled=false

# Копируем проиндексированные данные в директорию данных Elasticsearch
COPY --chown=elasticsearch:elasticsearch data/ /usr/share/elasticsearch/data

# Устанавливаем права доступа
RUN chmod -R 0775 /usr/share/elasticsearch/data

# Удаляем файлы блокировок (добавьте эти команды)
RUN find /usr/share/elasticsearch/data -type f -name "*.lock" -delete
RUN rm -f /usr/share/elasticsearch/data/nodes/0/node.lock
