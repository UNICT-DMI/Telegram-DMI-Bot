from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from module.shared import read_md

from datetime import date, datetime
import json
import dryscrape
import time
import pandas as pd
import calendar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

BACK_BUTTON_TEXT =  "Indietro ❌"

def updater_schedule(context):
    session = dryscrape.Session()
    aulario_url = read_md("aulario")
    session.visit(aulario_url)
    time.sleep(0.5)

    response = session.body()

    tables = pd.read_html(response)
    days = {}
    for k,table in enumerate(tables):
        rooms = table.iloc[:,0]
        schedule = table.iloc[:,1:]
        subjects = {}
        for c in schedule:
            for i,row in enumerate(table[c]):
                if not pd.isnull(row):
                    r = row[:20] + rooms[i]
                    if not r in subjects:
                        subjects[r] = {}

                        subjects[r]["subj"] = row.replace('[]','').replace('[','(').replace(']',')')
                        subjects[r]["times"] = []
                        subjects[r]['room'] = rooms[i]
                    if c[-1] == "1":
                        c = c[:3] + "30"
                    subjects[r]['times'].append(c)
        days[k] = subjects

    with open("data/json/subjs.json", "w+") as outfile:
        json.dump(days, outfile)


def get_json(file):
    try:
        json_file = open('data/json/{0}.json'.format(file),'r')
    except:
        return False

    return json.load(json_file)

def create_calendar(days,year=None,month=None):
    today = date.today()
    if year == None:
        year = today.year
    if month == None:
        month = today.month

    keyboard = []
    keyboard.append([InlineKeyboardButton("🗓 {0} {1}".format(calendar.month_name[month],str(year)),callback_data = "NONE")])
    week = ['L','M','M','G','V','S','D']
    row = []
    for w in week:
        row.append(InlineKeyboardButton(w,callback_data = "NONE"))
    keyboard.append(row)
    my_cal = calendar.monthcalendar(year,month)
    diff = 0
    for my_week in my_cal:
        row = []
        empty = True
        for day in my_week:
            if day < today.day and (day == 0 or month == today.month) :
                row.append(InlineKeyboardButton(" ",callback_data = "NONE"))
            else:
                curr = date(year,month,day)
                diff = (curr - today).days
                if diff < days:
                    empty = False
                    row.append(InlineKeyboardButton(str(day),callback_data = "cal_{0}".format(diff)))
                else:
                    row.append(InlineKeyboardButton(" ",callback_data = "NONE"))
        if not empty:
            keyboard.append(row)
    row = []
    if today.month < month or today.year < year:
        row.append(InlineKeyboardButton("◀️ {0}".format(calendar.month_name[((month-2)%12)+1]),callback_data="m_p_{0}_{1}_{2}".format(year,month,days)))
    if diff < days:
        row.append(InlineKeyboardButton("{0} ▶️".format(calendar.month_name[((month)%12)+1]),callback_data="m_n_{0}_{1}_{2}".format(year,month,days)))
    keyboard.append(row)
    return(InlineKeyboardMarkup(keyboard))


def aulario(update: Update, context: CallbackContext, chat_id=None, message_id=None):
    if not chat_id:
        chat_id = update.message.chat_id

    json_data = get_json("subjs")
    if json_data:
        keys =  [k for k in json_data.keys()]
        reply_markup = create_calendar(len(keys))
        text = "Seleziona la data della lezione che ti interessa."
        if message_id:
            context.bot.editMessageText(text = text, reply_markup = reply_markup , chat_id = chat_id, message_id = message_id)
        else:
            context.bot.sendMessage(text = text, reply_markup = reply_markup , chat_id = chat_id)
    else:
        text = "⚠️ Aulario non ancora pronto, riprova fra qualche minuto ⚠️"
        if message_id:
            context.bot.editMessageText(text = text, chat_id = chat_id, message_id = message_id)
        else:
            context.bot.sendMessage(text = text, chat_id = chat_id)
        context.job_queue.run_once(updater_schedule,0)
 
def aulario_subj(update: Update, context: CallbackContext, chat_id, message_id, day):
    json_data = get_json("subjs")
    if json_data[day]:
        text = "Quale lezione devi seguire?"

        keyboard = get_subjs_keyboard(0,day,json_data)
        keyboard.append([InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = 'sm_aulario')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.deleteMessage(chat_id = chat_id,  message_id = message_id)
        context.bot.sendMessage(text = text, reply_markup = reply_markup, chat_id = chat_id)
    elif json_data[day] == {}:
        text = "Nessuna lezione programmata per questo giorno"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = 'sm_aulario')]])

        context.bot.deleteMessage(chat_id = chat_id,  message_id = message_id)
        context.bot.sendMessage(text = text, reply_markup = reply_markup, chat_id = chat_id)

def get_subjs_keyboard(page,day,data):
    keys = data[day]
    subjs = list(keys)
    t_subjs = subjs
    if day == '0':
        t_subjs = []
        for s in subjs:
            t = keys[s]['times'][-1]
            h = t.split(':')[0]
            m = t.split(':')[1]
            now = datetime.now()
            last = now.replace(hour = int(h), minute = int(m), second = 0, microsecond = 0)
            if now < last:
                t_subjs.append(s)

    keyboard = []
    for s in t_subjs[page*5:(page*5)+5]:
        keyboard.append([InlineKeyboardButton(data[day][s]["subj"],callback_data = 'sb_{0}_{1}'.format(day,s))])

    arrows = []
    if page != 0:
        arrows.append(InlineKeyboardButton('◀️',callback_data = 'pg_{0}_{1}_l'.format(day,page)))
    if len(t_subjs) > page*5+5:
        arrows.append(InlineKeyboardButton('▶️',callback_data = 'pg_{0}_{1}_r'.format(day,page)))
    keyboard.append(arrows)
    return keyboard

def calendar_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    day = data.split("_")[1]
    aulario_subj(update, context, chat_id, message_id, day)


def month_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    d = data.split("_")
    direction = d[1]
    year = int(d[2])
    month = int(d[3])
    days = int(d[4])

    if direction == 'n':
        if month < 12:
            month += 1
        else:
            month = 1
            year += 1
    elif direction == 'p':
        if month > 1:
            month -= 1
        else:
            month = 12
            year -= 1

    context.bot.editMessageReplyMarkup(reply_markup = create_calendar(days,year,month), chat_id = chat_id, message_id = message_id)


def subjects_arrow_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    day = data.split('_')[1]
    page = int(data.split('_')[2])
    json_data = get_json("subjs")

    if data[-1] == 'r':
        page+=1
    elif data[-1] == 'l':
        page-=1

    keyboard = get_subjs_keyboard(page, day, json_data)
    keyboard.append([InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = 'sm_aulario')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageReplyMarkup(chat_id = query.message.chat_id,message_id=query.message.message_id,reply_markup = reply_markup)

def subjects_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    json_data = get_json("subjs")
    d = data.split("_")
    day = d[1]
    s = d[2]

    hours = json_data[day][s]['times']
    start = hours[0]
    end = hours[-1]
    if end[3:] == '30':
        end = "{0}:00".format(int(end[:2])+1)
    else:
        end = end[:3]+'30'

    h = "{0} - {1}".format(start,end)
    room = json_data[day][s]['room']
    sub = json_data[day][s]['subj']
    text = "{0} Ore: {1}: {2}".format(sub, h, room)
    photo = create_map(sub,h,room)

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data = 'sm&aulario_subj&{0}'.format(day))]])
    context.bot.deleteMessage(chat_id = chat_id,message_id = message_id)
    if not photo:
        context.bot.sendMessage(text = text, reply_markup = reply_markup, chat_id = chat_id)
    else:
        context.bot.sendPhoto(photo = photo, reply_markup = reply_markup, chat_id = chat_id)

def create_map(sub,h,room):
    data = get_json("room_coordinates")
    if room in data:
        b1_path = 'data/img/mappa.jpg'
        b1_img = Image.open(b1_path)
        draw = ImageDraw.Draw(b1_img)
        font = ImageFont.truetype("data/fonts/arial.ttf",30)
        draw.text((30,860),"{0} Ore: {1} ".format(sub,h),fill = 'black', font = font)
        coord = data[room]
        [x, y, w, z] = coord
        draw.rectangle((x, y, w, z), outline ='red', width = 5)
        bio = BytesIO()
        bio.name = 'image.jpeg'
        b1_img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
