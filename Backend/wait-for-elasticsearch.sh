#!/bin/sh

echo "Ожидание готовности Elasticsearch..."

# Проверяем доступность Elasticsearch
while ! curl -s http://elasticsearch:9200 > /dev/null; do
  sleep 5
done

echo "Elasticsearch готов. Запуск бэкенда..."

# Запускаем бэкенд
exec "$@"
