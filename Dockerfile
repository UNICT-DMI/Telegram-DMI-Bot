FROM python:3.10-slim
WORKDIR /dmibot/

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# web app dependencies & build
RUN curl -fsSL https://deb.nodesource.com/setup_19.x | bash - && apt-get install -y nodejs
RUN mkdir -p webapp/dist; cd webapp/; npm install; npx parcel build index.html; cd ..

COPY . .

ENTRYPOINT ["python3", "main.py"]
