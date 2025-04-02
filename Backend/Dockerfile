
FROM python:3.12


WORKDIR /app


COPY . .


RUN pip install -r requirements.txt


RUN chmod +x wait-for-elasticsearch.sh


CMD ["./wait-for-elasticsearch.sh", "python", "server.py"]
