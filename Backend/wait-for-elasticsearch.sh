#!/bin/sh

echo "Ожидание готовности Elasticsearch..."

while ! curl -s http://elasticsearch:9200 > /dev/null; do
  sleep 5
done

echo "Elasticsearch готов. Запуск бэкенда..."

exec "$@"
