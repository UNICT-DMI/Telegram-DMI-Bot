# encoding=utf8
import requests
import bs4
from os.path import exists, join
import xlrd
import datetime
from collections import OrderedDict
def scrap():

    url = "http://www.ersucatania.gov.it/menu-mensa/"

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    result = requests.get(url, headers=headers).content
    PATH = "data/"

    SECTION_ = "section"
    CLASS_ = "entry-content clearfix"

    soup = bs4.BeautifulSoup(result, "html.parser")

    try:
        menu = soup.find(SECTION_, class_= CLASS_).find_all("p")[1].find("a") # Contiene nome Menu
    except IndexError, ValueError:
        print "Errore mensa"
    nome_menu = menu.text;
    link_menu = menu.get("href")

    nome_file = nome_menu.lower().encode('utf-8').replace('ù', 'u').replace("menu",'').replace(' ','')+".xls"

    if (not exists(join(PATH,nome_file))): # not =  !
        #Il file non esiste, crealo
        result = requests.get(link_menu, headers=headers)
        f = open(PATH+nome_file, "wb")
        f1 = open(PATH+"mensa.xls","wb")
        f.write(result.content)
        f1.write(result.content)

def mensamessage(bot,update):

	wb = xlrd.open_workbook("data/mensa.xls")
	sh = wb.sheet_by_index(0)
	#Week menu
	weekx =  (2,8,14,21,28,35,41)
	weeky = (6,12,18,25,32,39,45)
	rprimi = range(weekx[datetime.date.today().weekday()] , weeky[datetime.date.today().weekday()])
	rsecont = range(weekx[datetime.date.today().weekday()], weeky[datetime.date.today().weekday()] + 1)

	if(datetime.datetime.hour < 15):
		cprimi = 1
		csecondi = 3
		ccontorni = 5
		ind =  "MENÙ PRANZO: %d/%d/%d \n" % (datetime.datetime.now().day, datetime.datetime.now().month,datetime.datetime.now().year) 
	else:
		cprimi = 7
		csecondi = 9
		ccontorni = 11
		ind = "MENÙ CENA: %d/%d/%d \n" % (datetime.datetime.now().day, datetime.datetime.now().month,datetime.datetime.now().year) 
	messagep = ""
	messages = ""
	messagec = ""
	#Orari mensa
	timemensa = "🕑 Orario Mensa \nPranzo dalle ore 12,15 alle ore 14,30 \nCena dalle ore 19,00 alle ore 21,30 \n "
	#Primi
	for count in rprimi:
		messagep += sh.cell(count,cprimi).value
		messagep += "\n"
	#Secondi
	for count in rsecont:
		messages += sh.cell(count,csecondi).value
		messages += "\n"
	#Contorni
	for count in rsecont:
		messagec += sh.cell(count,ccontorni).value
		messagec += "\n"
	
	bot.sendMessage(chat_id=update.message.chat_id, text = timemensa + "\n🍽" + ind + messagep+ "\n" + messages + "\n" + messagec)
