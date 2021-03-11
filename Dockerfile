FROM python:3.8.5-slim-buster

ARG TOKEN

WORKDIR /dmibot

RUN apt-get update && \
	apt-get install -y

COPY requirements.txt .
#Install requirements
RUN pip3 install -r requirements.txt

COPY . .
#Final setup settings and databases
RUN mv data/DMI_DB.db.dist data/DMI_DB.db &&\
	mv config/settings.yaml.dist config/settings.yaml &&\
	python3 setup.py ${TOKEN}

CMD ["python3", "main.py"]