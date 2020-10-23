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

- python-telegram-bot
- pydrive
- requests
- beautifulsoup4
- python-gitlab
- pytz
- pandas
- dryscrape

To install all the requirements you can run:
```bash
sudo apt install libqtwebkit-dev
pip3 install -r requirements.txt
```

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

### License
This open-source software is published under the GNU General Public License (GNU GPL) version 3. Please refer to the "LICENSE" file of this project for the full text.

### Contributors
You can find the list of contributors [here](CONTRIBUTORS.md)
