# Telegram-DMI-Bot

**Telegram-DMI-Bot** is the platform that powers **@DMI_bot**, a Telegram bot aided at helping students find informations about professors, classes' schedules, administration's office hours and more.

### Using the live version
The bot is live on Telegram with the username [@DMI_Bot](https://telegram.me/DMI_Bot).
Send **'/start'** to start it, **'/help'** to see a list of commands.

Please note that the commands and their answers are in Italian.

---

### Setting up a local instance
If you want to test the bot by creating your personal instance, follow this steps:
* **Clone this repository** or download it as zip.
* **Send a message to your bot** on Telegram, even '/start' will do. If you don't, you could get an error
* Make a copy of the file "data/DMI_DB.db.dist" in the same directory and rename it to "DMI_DB.db" to enable the database sqlite
* Make a copy of the file "config/settings.yaml.dist" in the same directory and rename it to "settings.yaml" (If you don't have a token, message Telegram's [@BotFather](http://telegram.me/Botfather) to create a bot and get a token for it)
* Now you can launch "main.py" with your Python3 interpreter

### System requirements

- Python 3
- python-pip3
- language-pack-it
- libqtwebkit (v5)

#### To install with *pip3*

- python-telegram-bot==12.8
- pydrive
- requests
- beautifulsoup4
- python-gitlab
- pytz
- pandas
- dryscrape
- pillow

To install all the requirements you can run:
```bash
sudo apt install libqtwebkit-dev
pip3 install -r requirements.txt
```

### Known problems on Ubuntu 20.04:

* #### **Installing libqtwebkit**

Open terminal in your repo folder and run command: 

```bash 
sudo add-apt-repository ppa:rock-core/qt4
```

After adding the PPA, it should automatically refresh the system package cache. If not, you may run command to manually update the package cache:

```bash
sudo apt update
```
  
  
  
* #### **Installing dryscrape**

Download webkit-server from github:

```bash
git clone https://github.com/niklasb/webkit-server.git webkit-server
```

Change in webkit-server/setup.py :

```python
shutil.copy('src/webkit_server', self.build_purelib)
shutil.copy('src/webkit_server', self.build_platlib)
```

to

```python
shutil.copy('src/webkit_server.pro', self.build_purelib)
shutil.copy('src/webkit_server.pro', self.build_platlib)
```

then run:

```bash
cd webkit-server
python setup.py install
```

- [x] There you go!




### Special functions

Notes: only some users are allowed to use these commands indeed there is an if condition that check the chatid of the user that can use them

#### - /stats
You can enable these commands setting **disable_db = 0** and copy **data/DMI_DB.db.dist** into **data/DMI_DB.db**

This command shows the statistics of the times where the commands are used in the last 30 days.

#### - /drive /request /adddb
You can enable these commands setting **disable_drive = 0**, configure the GoogleDrive credentials and copy **data/DMI_DB.db.dist** into **data/DMI_DB.db**.

**/drive**: command to get the GoogleDrive files
**/request** allows the user to send the subscribe request to get the access for /drive
**/adddb** allows some special users to give the access to /drive to another user

##### **Configure Drive**
- open a project on the Google Console Developer
- enable Drive API
- download the drive_credentials.json and put it on config/
- copy **config/settings.yaml.dist** into **config/settings.yaml**, then configure it

### Docker container

#### How to use
Build image dmibot with docker:

```
$ docker build ./ -t dmibot --build-arg TOKEN=<token_API>
```

Run the container dmibot:

```
$ docker run -it dmibot
```

Now you can go to the dmibot directory and run the bot:

```
$ cd /usr/local/dmibot/
$ python main.py
```

Note: if you need to run the main.py in a VPS, you will need now xvfb-run to run it (`xvfb-run python3 main.py`), because **dryscrape** requires it.

### Testing

#### To install with *pip3*

- pytest
- pytest-asyncio
- telethon

To install all the test requirements you can run:
```bash
pip3 install -r test-requirements.txt
```

Steps:
- Sign in your Telegram account with your phone number **[here](https://my.telegram.org/auth)**. Then choose “API development tools”
- If it is your first time doing so, it will ask you for an app name and a short name, you can change both of them later if you need to. Submit the form when you have completed it
- You will then see the api_id and api_hash for your app. These are unique to your app, and not revocable.
- Edit the folling values in the config/settings.yaml file:
```yaml
test: 
  api_hash: hash of the telegram app used for testing
  api_id: id of the telegram app used for testing
  session: session of the telegram app used for testing (see steps below)
  tag: tag of the bot used for testing
  token: token for the bot used for testing
  representatives_group: representatives' group id used for testing
  dev_group_chatid: dev's group id used for testing
```
- Copy the file "tests/conftest.py" in the root folder and Run 
```bash
python3 conftest.py .
```
- Follow the procedure and copy the session value it provides in the settings file in "test:session". You can then delete the "conftest.py" you just used, you won't need it again
- Edit the remaining values in the settings file as you like

**Check [here](https://dev.to/blueset/how-to-write-integration-tests-for-a-telegram-bot-4c0e) if you want to have more information on the steps above**

Start tests:
```bash
pytest
```

### License
This open-source software is published under the GNU General Public License (GNU GPL) version 3. Please refer to the "LICENSE" file of this project for the full text.

### Contributors
You can find the list of contributors [here](CONTRIBUTORS.md)
If you want to contribute, make sure to read the [guidelines](CONTRIBUTING.md)
