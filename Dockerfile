FROM python:3.10-slim
WORKDIR /dmibot/

# web app dependencies & build
RUN  apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir -p webapp/dist; cd webapp/; npm install; npx parcel build index.html; cd ..

ENTRYPOINT ["python3", "main.py"]
