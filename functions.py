# -*- coding: utf-8 -*-

#Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler, RegexHandler

#Drive
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

#Custom classes
from classes.StringParser import StringParser

#System libraries
from datetime import date, datetime, timedelta
import json,datetime,re,random,os,sys
import requests
import urllib2
from bs4 import BeautifulSoup
import sqlite3
import logging

from module.lezioni import lezioni_cmd
from module.esami import esami_cmd
from module.professori import prof_cmd

# Debug
disable_chatid_logs = 1 #news, stats
disable_db = 1          #stats, drive
disable_drive = 1       #drive

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

conn = sqlite3.connect('data/DMI_DB.db',check_same_thread=False)

#Token
tokenconf = open('config/token.conf', 'r').read()
tokenconf = tokenconf.replace("\n", "")
TOKEN = tokenconf    		#Token of your telegram bot that you created from @BotFather, write it on token.conf

def lezioni(bot, update, args, *m):
    checkLog(bot, update, "lezioni")
    if(m):
        messageText = "_Command under development._\nControlla la risorsa da te richiesta sul [sito](http://web.dmi.unict.it/Didattica/Laurea%20Magistrale%20in%20Informatica%20LM-18/Calendario%20delle%20Lezioni)"
    else:
        messageText = lezioni_cmd(args, 'http://188.213.170.165/PHP-DMI-API/result/lezioni_dmi.json')
    bot.sendMessage(chat_id=update.message.chat_id, text=messageText, parse_mode='Markdown')

def esami(bot, update, args, *m):
    checkLog(bot, update, "esami")
    if(m):
        messageText = "_Command under development._\nControlla la risorsa da te richiesta sul [sito](http://web.dmi.unict.it/Didattica/Laurea%20Magistrale%20in%20Informatica%20LM-18/Calendario%20degli%20Esami)"
    else:
        messageText = esami_cmd(args, 'http://188.213.170.165/PHP-DMI-API/result/esami_dmi.json')
    bot.sendMessage(chat_id=update.message.chat_id, text=messageText, parse_mode='Markdown')

def forum(sezione):

    response = urllib2.urlopen("http://forum.informatica.unict.it/")
    html_doc = response.read()

    #print(html_doc)
    s = BeautifulSoup(html_doc, 'html.parser')
    s.prettify()
    dictionary = {}
    for rangeLimit,mainTable in enumerate(s.findAll("div", class_="tborder")):
        if(rangeLimit >= 3): #If che limita le sezioni a quelle interessate, evitando di stampare sottosezioni come "News" della categoria "Software"
            break
        for tdOfTable in mainTable.findAll("td", class_="windowbg3"):
            for spanUnder in tdOfTable.findAll("span", class_="smalltext"):
                for anchorTags in spanUnder.find_all('a'):
                    anchorTagsSplitted = anchorTags.string.split(",")
                    anchorTagsWithoutCFU = StringParser.removeCFU(anchorTagsSplitted[0])

                    if(sezione == anchorTagsWithoutCFU.lower()):
                        dictionary[anchorTagsWithoutCFU.lower()] = anchorTags['href']
                        return dictionary

    return False #Redefine with @Veeenz API

# Commands
CUSicon = {0 : "🏋",
	   1 : "⚽️",
	   2 : "🏀",
	   3 : "🏈",
	   4 : "🏐",
	   5 : "🏊",
}

def help_cmd():
    output = "@DMI_Bot risponde ai seguenti comandi: \n\n"
    output += "📖 /esami - /mesami - 	linka il calendario degli esami\n"
    output += "🗓 /aulario - linka l\'aulario\n"
    output += "👔 /prof <nome> - es. /prof Milici\n"
    output += "🍽 /mensa - orario mensa\n"
    output += "👥 /rappresentanti - elenco dei rappresentanti del DMI\n"
    output += "📚 /biblioteca - orario biblioteca DMI\n"
    output += CUSicon[random.randint(0,5)] + " /cus sede e contatti\n\n"
    output += "Segreteria orari e contatti:\n"
    output += "/sdidattica - segreteria didattica\n"
    output += "/sstudenti - segreteria studenti\n"
    output += "/cea - CEA\n"
    output += "\nERSU orari e contatti\n"
    output += "/ersu - sede centrale\n"
    output += "/ufficioersu - (ufficio tesserini)\n"
    output += "/urp - URP studenti\n\n"
    output += "~Bot~\n"
    output += "📂 /drive - accedi a drive\n"
    output += "/disablenews \n"
    output += "/enablenews\n"
    output += "/contributors"
    return output

def read_md(namefile):
    in_file = open("data/markdown/" + namefile + ".md","r")
    text = in_file.read()
    in_file.close()
    return text

def informative_callback(bot, update, cmd):
    checkLog(bot, update, cmd)
    messageText = read_md(cmd)
    bot.sendMessage(chat_id=update.message.chat_id, text=messageText, parse_mode='Markdown')

def enablenews_cmd():
	output = "Per confermare l'iscrizione alla newsletter del DMI digita /enablenews"
	return output

def disablenews_cmd():
	output = "Se sei sicuro di voler disiscriverti dalla newsletter del DMI digita /disablenews"
	return output

def exit_cmd():
	output = "."
	return output

def esami_button():
	output = "Scrivi /esami inserendo almeno uno dei seguenti parametri: giorno, materia, sessione (prima, seconda, terza, straordinaria)"
	return output

def lezioni_button():
	output = "Scrivi /lezioni inserendo almeno uno dei seguenti parametri: giorno, materia"
	return output

def mesami_url():
	url = "http://web.dmi.unict.it/Didattica/Laurea%20Magistrale%20in%20Informatica%20LM-18/Calendario%20degli%20Esami"
	return url

def aulario_url():
	url = 'http://aule.dmi.unict.it/aulario/roschedule.php'
	return url

#Easter egg
def smonta_portoni_cmd():
	r = random.randint(0,13)
	if (r >= 0 and r <= 3):
		output = "$ sudo umount portoni"
	elif (r > 3 and r < 10):
		output = "@TkdAlex"
	elif (r == 11):
		output = "https://s16.postimg.org/5a6khjb5h/smonta_portoni.jpg"
	else:
		output = "https://s16.postimg.org/rz8117y9x/idraulico.jpg"
	return output

def santino_cmd():
    r = random.randint(0,20)
    if (r >= 0 and r <= 3):
        output = "@Santinol"
    elif (r > 3 and r < 10):
        output = "https://s18.postimg.org/t13s9lai1/photo_2016_11_24_11_04_42.jpg"
    elif (r >= 10 and r < 16):
		output = "https://s11.postimg.org/yiwugh4ib/photo_2016_11_24_11_04_31.jpg"
    elif (r >=16 and r < 21):
        output = "https://s12.postimg.org/5d7y88pj1/photo_2016_11_24_11_04_29.jpg"

    return output

def prof_sticker_id(data):
	text = json.loads(open(data).read())
	i=random.randint(0,len(text))
	return text[i]["id"]

def forum_cmd(text):
	text = text.replace("/forum ","")
	dictUrlSezioni = forum(text)
	if not (dictUrlSezioni == False):
		for titoli in dictUrlSezioni:
			output = StringParser.startsWithUpper(titoli)+": "+str(dictUrlSezioni[titoli])
	else:
		output = "La sezione non e' stata trovata."
	return output

def callback(bot, update):
	keyboard2=[[]];
	icona=""
	NumberRow=0
	NumberArray=0
	update_id = update.update_id

	update.callback_query.data = update.callback_query.data.replace("Drive_", "")

	if len(update.callback_query.data)<13:
		#conn.execute("DELETE FROM 'Chat_id_List'")
		ArrayValue=update['callback_query']['message']['text'].split(" ")
		try:
			if len(ArrayValue)==5:
				conn.execute("INSERT INTO 'Chat_id_List' VALUES ("+update.callback_query.data+",'"+ArrayValue[4]+"','"+ArrayValue[1]+"','"+ArrayValue[2]+"','"+ArrayValue[3]+"') ")
				bot.sendMessage(chat_id=update.callback_query.data,text= "🔓 La tua richiesta è stata accettata")
				bot.sendMessage(chat_id=-1001095167198,text=str(ArrayValue[1])+" "+str(ArrayValue[2]+str(" è stato inserito nel database")))

			elif len(ArrayValue)==4:
				conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES ("+update.callback_query.data+",'"+ArrayValue[1]+"','"+ArrayValue[2]+"','"+ArrayValue[3]+"')")
				bot.sendMessage(chat_id=update.callback_query.data,text= "🔓 La tua richiesta è stata accettata")

			else:
				bot.sendMessage(chat_id=-1001095167198,text=str("ERRORE INSERIMENTO: ")+str(update['callback_query']['message']['text'])+" "+str(update['callback_query']['data']))
			conn.commit()
		except Exception as error:
			bot.sendMessage(chat_id=-1001095167198,text=str("ERRORE INSERIMENTO: ")+str(update['callback_query']['message']['text'])+" "+str(update['callback_query']['data']))

		LAST_UPDATE_ID = update_id + 1
		text = ""
		messageText = ""

	else:
		if(os.fork()==0):
			settings_file = "config/settings.yaml"
			gauth2 = GoogleAuth(settings_file=settings_file)
			gauth2.CommandLineAuth()
			#gauth2.LocalWebserverAuth()
			drive2 = GoogleDrive(gauth2)
			bot2 = telegram.Bot(TOKEN)

			file1=drive2.CreateFile({'id':update.callback_query.data})
			if file1['mimeType']=="application/vnd.google-apps.folder":
				file_list2= drive2.ListFile({'q': "'"+file1['id']+"' in parents and trashed=false",'orderBy':'folder,title'}).GetList()
				for file2 in file_list2:

					fileN=""

					if file2['mimeType']=="application/vnd.google-apps.folder":
						if NumberRow>=1:
							keyboard2.append([InlineKeyboardButton("🗂 "+file2['title'], callback_data="Drive_" + file2['id'])])
							NumberRow=0
							NumberArray+=1
						else:
							keyboard2[NumberArray].append(InlineKeyboardButton("🗂 "+file2['title'], callback_data="Drive_" + file2['id']))
							NumberRow+=1
					else:
						if  ".pdf" in file2['title']:
							icona="📕 "
						elif ".doc" in file2['title'] or ".docx" in file2['title'] or ".txt" in file2['title'] :
							icona="📘 "
						elif ".jpg" in file2['title'] or ".png" in file2['title'] or ".gif" in  file2['title']:
							icona="📷 "
						elif ".rar" in file2['title'] or ".zip" in file2['title']:
							icona="🗄 "
						elif ".out" in file2['title'] or ".exe" in file2['title']:
							icona="⚙ "
						elif ".c" in file2['title'] or ".cpp" in file2['title'] or ".py" in file2['title'] or ".java" in file2['title'] or ".js" in file2['title'] or ".html" in file2['title'] or ".php" in file2['title']:
							icona="💻 "
						else:
							icona="📄 "
						if NumberRow>=1:
							keyboard2.append([InlineKeyboardButton(icona+file2['title'], callback_data="Drive_" + file2['id'])])
							NumberRow=0
							NumberArray+=1
						else:
							keyboard2[NumberArray].append(InlineKeyboardButton(icona+file2['title'], callback_data="Drive_" + file2['id']))
							NumberRow+=1

				if file1['parents'][0]['id'] != '0ADXK_Yx5406vUk9PVA':
					keyboard2.append([InlineKeyboardButton("🔙", callback_data="Drive_" + file1['parents'][0]['id'])])
				reply_markup3 = InlineKeyboardMarkup(keyboard2)
				bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'],text=file1['title']+":", reply_markup=reply_markup3)

			elif file1['mimeType'] == "application/vnd.google-apps.document":
				bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Impossibile scaricare questo file poichè esso è un google document, Andare sul seguente link")
				bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file1['exportLinks']['application/pdf'])

			else:
				try:
					fileD=drive2.CreateFile({'id':file1['id']})
					if int(fileD['fileSize']) < 5e+7:
						fileD.GetContentFile('file/'+file1['title'])
						fileS=file1['title']
						filex=open(str("file/"+fileS),"rb")
						bot2.sendChatAction(chat_id=update['callback_query']['from_user']['id'], action="UPLOAD_DOCUMENT")
						bot2.sendDocument(chat_id=update['callback_query']['from_user']['id'], document=filex)
						os.remove(str("file/"+fileS))
					else:
						bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="File troppo grande per il download diretto, scarica dal seguente link")
						bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'],text=fileD['alternateLink']) ##fileD['downloadUrl']
				except Exception as e:
					print str(e)
					bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'],text="Impossibile scaricare questo file, contattare gli sviluppatori del bot")
					open("logs/errors.txt","a+").write(str(e)+str(fileD['title'])+"\n")

			sys.exit(0)

def request(bot, update):
	chat_id = update.message.chat_id
	flag=0
	if (chat_id>0):
		for row in conn.execute("SELECT Chat_id FROM Chat_id_List"):
			if row[0] == chat_id:
				flag=1

		if flag==0:
			messageText="✉️ Richiesta inviata"
			keyboard=[[]]
			if (update['message']['from_user']['username']):
				username= update['message']['from_user']['username']
			else:
				username=""
			if(len(update.message.text.split(" "))==4) and ("@" in update.message.text.split(" ")[3]) and ("." in update.message.text.split( )[3]):
				textSend=str(update.message.text)+" "+username
				keyboard.append([InlineKeyboardButton("Accetta", callback_data="Drive_"+str(chat_id))])
				reply_markup2=InlineKeyboardMarkup(keyboard)
				bot.sendMessage(chat_id=-1001095167198,text=textSend,reply_markup=reply_markup2)
				bot.sendMessage(chat_id=chat_id, text=messageText)

			else:
				messageText="Errore compilazione /request:\n Forma esatta: /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro)"
				bot.sendMessage(chat_id=update.message.chat_id, text=messageText)


		else:
			messageText="Hai già effettuato la richiesta di accesso"
			bot.sendMessage(chat_id=update.message.chat_id, text=messageText)

	else:
		messageText="Non è possibile utilizzare /request in un gruppo"
		bot.sendMessage(chat_id=chat_id, text=messageText)

def adddb(bot, update):
	chat_id = update.message.chat_id
	if (chat_id==26349488 or chat_id==-1001095167198 or chat_id==46806104):
		ArrayValue=update.message.text.split(" ") #/add nome cognome e-mail username chatid
		if len(ArrayValue)==6:
			conn.execute("INSERT INTO 'Chat_id_List' VALUES ("+ArrayValue[5]+",'"+ArrayValue[4]+"','"+ArrayValue[1]+"','"+ArrayValue[2]+"','"+ArrayValue[3]+"') ")
			bot.sendMessage(chat_id=ArrayValue[5],text= "🔓 La tua richiesta è stata accettata")
			conn.commit()
		elif len(ArrayValue)==5:
			conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES ("+ArrayValue[4]+",'"+ArrayValue[1]+"','"+ArrayValue[2]+"','"+ArrayValue[3]+"')")
			bot.sendMessage(chat_id=int(ArrayValue[4]),text= "🔓 La tua richiesta è stata accettata")
			conn.commit()
		else:
			bot.sendMessage(chat_id=chat_id,text="/adddb <nome> <cognome> <e-mail> <username> <chat_id>")

def drive(bot, update):
    checkLog(bot, update, "drive")

    settings_file = "config/settings.yaml"
    gauth = GoogleAuth(settings_file=settings_file)
    gauth.CommandLineAuth()
    #gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    chat_id=update.message.chat_id
    TestDB=0
    IDDrive='0B7-Gi4nb88hremEzWnh3QmN3ZlU'
    if chat_id < 0:
    	bot.sendMessage(chat_id=chat_id,text="La funzione /drive non è ammessa nei gruppi")
    else:
    	for row in conn.execute("SELECT Chat_id FROM 'Chat_id_List' "):
    		if row[0] == chat_id:
    			TestDB=1;

    	if TestDB==1:
            keyboard2=[[]];
            try:
                file_list = drive.ListFile({'q': "'"+IDDrive+"' in parents and trashed=false",'orderBy':'folder,title'}).GetList()
            except Exception as error:
                print str(error)
            NumberRow=0
            NumberArray=0

            for file1 in file_list:
                fileN=""
                if file1['mimeType']=="application/vnd.google-apps.folder":
                    if NumberRow>=3:
                        keyboard2.append([InlineKeyboardButton("🗂 "+file1['title'], callback_data="Drive_" + file1['id'])])
                        NumberRow=0
                        NumberArray+=1
                    else:
                        keyboard2[NumberArray].append(InlineKeyboardButton("🗂 "+file1['title'],callback_data="Drive_" + file1['id']))
                        NumberRow+=1
                else:
                    if NumberRow>=3:
                        keyboard2.append([InlineKeyboardButton("📃 "+file1['title'], callback_data="Drive_" + file1['id'])])
                        NumberRow=0
                        NumberArray+=1
                    else:
                        keyboard2[NumberArray].append(InlineKeyboardButton("📃 "+file1['title'],callback_data="Drive_" + file1['id']))
                        NumberRow+=1

            reply_markup3 = InlineKeyboardMarkup(keyboard2)
            bot.sendMessage(chat_id=chat_id,text="DMI UNICT - Appunti & Risorse:", reply_markup=reply_markup3)
    	else:
    		bot.sendMessage(chat_id=chat_id,text="🔒 Non hai i permessi per utilizzare la funzione /drive,\n Utilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro) ")


# CallbackQueryHandler
def button_handler(bot, update):
	query = update.callback_query
	chat_id = query.message.chat_id
	message_id = query.message.message_id
	data = query.data

	#Submenu
	if data.startswith("sm_"):
		funcName = data[3:len(data)]

		globals()[funcName](bot, chat_id, message_id)

	elif data == "esami_button" or data == "lezioni_button" or data == "help_cmd" or data == "exit_cmd":
		messageText = globals()[data]()
		bot.editMessageText(text=messageText, chat_id=chat_id, message_id=message_id)

	elif data.startswith("Drive_"):
		callback(bot,update)

	#Simple text
	elif data != "_div":
		messageText = read_md(data)
		checkLog(bot, update, data, 1)
		bot.editMessageText(text=messageText, chat_id=chat_id, message_id=message_id)

def help(bot, update):
	checkLog(bot, update, "help")

	chat_id = update.message.chat_id
	keyboard=[[]]
	messageText="@DMI_Bot risponde ai seguenti comandi:"

	keyboard.append([InlineKeyboardButton(" ~ Dipartimento e CdL ~ ", callback_data="_div")])

	keyboard.append(
		[
			InlineKeyboardButton("📖 Esami (Triennale)",   callback_data="esami_button"),
			InlineKeyboardButton("📖 Esami (Magistrale)",  url=mesami_url()),
			InlineKeyboardButton("🗓 Aulario",             url=aulario_url()),
			InlineKeyboardButton("Lezioni",               callback_data="lezioni_button")
		]
	)
	keyboard.append(
		[
			InlineKeyboardButton("🍽 Mensa",                             callback_data="mensa"),
			InlineKeyboardButton("👥 Rappresentanti",                    callback_data="sm_rapp_menu"),
			InlineKeyboardButton("📚 Biblioteca",                        callback_data="biblioteca"),
			InlineKeyboardButton(CUSicon[random.randint(0,5)] + " CUS", callback_data="cus")
		]
	)

	keyboard.append([InlineKeyboardButton(" ~ Segreteria orari e contatti ~ ", callback_data="_div")])

	keyboard.append(
		[
			InlineKeyboardButton("Seg. Didattica",  callback_data="sdidattica"),
			InlineKeyboardButton("Seg. Studenti",   callback_data="sstudenti"),
			InlineKeyboardButton("CEA",             callback_data="cea")
		]
	)

	keyboard.append([InlineKeyboardButton(" ~ ERSU orari e contatti ~ ", callback_data="_div")])

	keyboard.append(
		[
			InlineKeyboardButton("ERSU",          callback_data="ersu"),
			InlineKeyboardButton("Ufficio ERSU",  callback_data="ufficioersu"),
			InlineKeyboardButton("URP",           callback_data="urp")
		]
	)

	keyboard.append([InlineKeyboardButton(" ~ Bot e varie ~ ", callback_data="_div")])

	keyboard.append(
		[
			InlineKeyboardButton("Iscriviti alle news",     callback_data="enablenews"),
			InlineKeyboardButton("Disiscriviti dalle news", callback_data="disablenews")
		]
	)
	keyboard.append(
		[
			InlineKeyboardButton("📂 Drive",          callback_data="drive"),
			InlineKeyboardButton("Contributors",     callback_data="contributors"),
		]
	)

	keyboard.append(
		[
			InlineKeyboardButton("Tutti i comandi", callback_data="help_cmd"),
			InlineKeyboardButton("Chiudi",          callback_data="exit_cmd")
		]
	)

	reply_markup=InlineKeyboardMarkup(keyboard)

	bot.sendMessage(chat_id=chat_id, text=messageText, reply_markup=reply_markup)

def rapp_menu(bot, chat_id, message_id):
	keyboard=[[]]
	messageText="Quali rappresentanti vuoi contattare?"

	keyboard.append(
		[
			InlineKeyboardButton("Rapp. DMI",         callback_data="rappresentanti_dmi"),
			InlineKeyboardButton("Rapp. Informatica", callback_data="rappresentanti_informatica"),
			InlineKeyboardButton("Rapp. Matematica",  callback_data="rappresentanti_matematica"),
		]
	)

	reply_markup=InlineKeyboardMarkup(keyboard)


	bot.editMessageText(text=messageText, chat_id=chat_id, message_id=message_id,reply_markup=reply_markup)

def smonta_portoni(bot, update):
	checkLog(bot, update,"smonta_portoni")
	messageText = smonta_portoni_cmd()
	bot.sendMessage(chat_id=update.message.chat_id, text= messageText)

def santino(bot, update):
	checkLog(bot, update,"santino")
	messageText = santino_cmd()
	bot.sendMessage(chat_id=update.message.chat_id, text= messageText)

def prof_sticker(bot,update):
	checkLog(bot,update,"prof_sticker")
	bot.sendSticker(chat_id=update.message.chat_id,sticker=prof_sticker_id('data/json/stickers.json'))

def prof(bot, update, args):
	checkLog(bot, update, "prof")
	messageText = prof_cmd(args)
	bot.sendMessage(chat_id=update.message.chat_id, text=messageText, parse_mode='Markdown')

def forum_bot(bot, update):
	checkLog(bot, update,"forum_bot")
	messageText = forum_cmd(update.message.text)
	bot.sendMessage(chat_id=update.message.chat_id, text= messageText)

def news_(bot, update):
	if (update.message.chat_id == 26349488 or update.message.chat_id == 37967664):
		global news
		news = update.message.text.replace("/news ", "")
		messageText = "News Aggiornata!"
		bot.sendMessage(chat_id=update.message.chat_id, text= messageText)

def spamnews(bot, update):
	if(update.message.chat_id==26349488):
		chat_ids = open('logs/chatid.txt', 'r').read()
		chat_ids = chat_ids.split("\n")
		for i in range((len(chat_ids)-1)):
			try:
				if not "+" in chat_ids[i]:
					bot.sendMessage(chat_id=chat_ids[i], text=news)
			except Exception as error:
				open("logs/errors.txt", "a+").write(str(error)+" "+str(chat_ids[i])+"\n")
		messageText = "News spammata!"
		bot.sendMessage(chat_id=update.message.chat_id, text= messageText)

def disablenews(bot, update):
	checkLog(bot, update,"disablenews")
	chat_ids = open('logs/chatid.txt', 'r').read()
	chat_id = update.message.chat_id
	if not ("+"+str(chat_id)) in chat_ids:
		chat_ids = chat_ids.replace(str(chat_id), "+"+str(chat_id))
		messageText= "News disabilitate!"
		open('logs/chatid.txt', 'w').write(chat_ids)
	else:
		messageText = "News già disabilitate!"
	bot.sendMessage(chat_id=update.message.chat_id, text= messageText)

def enablenews(bot, update):
	checkLog(bot, update,"enablenews")
	chat_ids = open('logs/chatid.txt', 'r').read()
	chat_id = update.message.chat_id
	if ("+"+str(chat_id)) in chat_ids:
		chat_ids = chat_ids.replace("+"+str(chat_id), str(chat_id))
		messageText = "News abilitate!"
		open('logs/chatid.txt', 'w').write(chat_ids)
	else:
		messageText = "News già abilitate!"
	bot.sendMessage(chat_id=update.message.chat_id, text= messageText)
	
# check if user (chatid) is registered on chatid.txt

def stats(bot, update):
    chat_id = update.message.chat_id
    conn = sqlite3.connect('data/DMI_DB.db',check_same_thread=False)
    if(len(update['message']['text'].split(' '))==2):
        days=int(update['message']['text'].split(' ')[1])
        if(days<=0):
            days=30
    else:
        days=30
    text=""
    dateCheck=unicode(date.today()-timedelta(days=days))
    text+="Record di "+str(days)+" giorni:\n"
    for row in conn.execute("SELECT Type, count(chat_id) FROM stat_list WHERE DateCommand > '"+dateCheck+"' GROUP BY Type ORDER BY Type;" ):
        text+=str(row[1])+": "+str(row[0])+"\n"
    bot.sendMessage(chat_id=chat_id,text=text)

def statsTot(bot, update):
    chat_id = update.message.chat_id
    conn = sqlite3.connect('data/DMI_DB.db',check_same_thread=False)
    text=""
    text+="Record Globale:\n"
    for row in conn.execute("SELECT Type, count(chat_id) FROM stat_list GROUP BY Type ORDER BY Type;" ):
        text+=str(row[1])+": "+str(row[0])+"\n"
    bot.sendMessage(chat_id=chat_id,text=text)

def checkLog(bot, update, type, callback=0):

    if callback:
      update = update.callback_query

    if (disable_db == 0):
        chat_id = update.message.chat_id
        conn = sqlite3.connect('data/DMI_DB.db',check_same_thread=False)
        today=unicode(date.today());
        conn.execute("INSERT INTO stat_list VALUES ('"+str(type)+"',"+str(chat_id)+",'"+str(today)+" ')");
        conn.commit()

    if (disable_chatid_logs == 0):
        log = open("logs/chatid.txt", "a+")
        if not str(chat_id) in log.read():
            log.write(str(chat_id)+"\n")

