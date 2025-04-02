#!/bin/sh

echo "Waiting for Elasticsearch..."

while ! curl -s http://elasticsearch:9200 > /dev/null; do
  sleep 5
done

echo "Elasticsearch is ready. Starting backend..."

exec "$@"
