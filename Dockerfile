FROM python:3.15-rc-slim
LABEL org.opencontainers.image.source=https://github.com/UNICT-DMI/Telegram-DMI-Bot
LABEL org.opencontainers.image.description="Telegram bot for the DMI students (@DMI_Bot)"
LABEL org.opencontainers.image.licenses=GPL-3.0
WORKDIR /dmibot/

# web app dependencies & build
RUN  apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && apt-get install -y nodejs

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir -p webapp/dist; cd webapp/; npm install; npx parcel build index.html; cd ..

ENTRYPOINT ["python3", "main.py"]
