FROM  ubuntu:20.04

ARG TOKEN
ENV DMI_BOT_REPO    https://github.com/UNICT-DMI/Telegram-DMI-Bot.git
ENV DMI_BOT_DIR    /usr/local

#Fix to install software-properties-common, needed to use add-apt-repository
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
	apt-get install -y \
	git \
	git-lfs \
	python3 \
	python3-pip\
	language-pack-it\
	software-properties-common

#Fix libqtwebkit-dev missing
RUN add-apt-repository ppa:rock-core/qt4 -y && apt-get install -y libqtwebkit-dev

#Fix webkit-server
RUN git clone https://github.com/niklasb/webkit-server.git /usr/local/webkit-server
RUN sed -i 's;src/webkit_server;src/webkit_server.pro;g' /usr/local/webkit-server/setup.py
RUN cd /usr/local/webkit-server/ && python3 setup.py install

RUN mkdir -p $DMI_BOT_DIR && \
	cd $DMI_BOT_DIR && \
	git clone -b master $DMI_BOT_REPO dmibot

RUN pip3 install -r $DMI_BOT_DIR/dmibot/requirements.txt

RUN cp $DMI_BOT_DIR/dmibot/data/DMI_DB.db.dist $DMI_BOT_DIR/dmibot/data/DMI_DB.db
RUN cp $DMI_BOT_DIR/dmibot/config/settings.yaml.dist $DMI_BOT_DIR/dmibot/config/settings.yaml
#RUN echo $TOKEN > $DMI_BOT_DIR/dmibot/config/token.conf
RUN sed -i "1 s/^token: \"\"/token: \"$TOKEN\"/" $DMI_BOT_DIR/dmibot/config/settings.yaml
