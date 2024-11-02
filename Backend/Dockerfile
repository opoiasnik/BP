# Используем базовый образ Python
FROM python:3.12

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем все файлы проекта в контейнер
COPY . .

# Устанавливаем зависимости из requirements.txt
RUN pip install -r requirements.txt

# Делаем скрипт ожидания исполняемым
RUN chmod +x wait-for-elasticsearch.sh

# Запускаем скрипт ожидания перед запуском бэкенда
CMD ["./wait-for-elasticsearch.sh", "python", "server.py"]
