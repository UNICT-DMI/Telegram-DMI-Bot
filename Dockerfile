FROM python:3.10-slim
WORKDIR /dmibot/

COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN mkdir -p webapp/dist

COPY . .

ENTRYPOINT ["python3", "main.py"]
