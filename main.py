# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import Bot, Update
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, Filters, CallbackContext, MessageHandler

# Modules
from module.easter_egg_func import smonta_portoni, santino, prof_sticker, bladrim, lei_che_ne_pensa_signorina
from module.callback_handlers import informative_callback, generic_button_handler, submenu_handler, md_handler, callback, submenu_with_args_handler, none_handler
from module.shared import config_map, TOKEN, give_chat_id, HELP, AULARIO, SEGNALAZIONE, CLOUD
from module.regolamento_didattico import regolamenti, regolamentodidattico, regolamentodidattico_button, triennale, magistrale, regdid
from module.esami import esami, esami_handler, esami_input_insegnamento
from module.lezioni import lezioni, lezioni_handler, lezioni_input_insegnamento
from module.professori import prof
from module.help import help
from module.gitlab import git, gitlab_handler
from module.gdrive import drive
from module.request import request, add_db
from module.report import report
from module.stats import stats, stats_tot
from module.job_updater import updater_lep
from module.utils.send_utils import send_chat_ids, send_errors, send_log
from module.aulario import aulario, calendar_handler, month_handler, subjects_handler, subjects_arrow_handler, updater_schedule
from start import start

# Utils
from datetime import time

bot = telegram.Bot(config_map["token"])


def logging_message(update: Update, context: CallbackContext):
	try:
		message_id = update.message.message_id #ID MESSAGGIO
		user = update.message.from_user # Restituisce un oggetto Telegram.User
		chat = update.message.chat # Restituisce un oggetto Telegram.Chat
		text = update.message.text #Restituisce il testo del messaggio
		date = update.message.date #Restituisce la data dell'invio del messaggio
		message = "\n___ID MESSAGE: " 	+ str(message_id) + "____\n" + \
					"___INFO USER___\n" + \
					"user_id:" 			+ str(user.id) + "\n" + \
					"user_name:" 			+ str(user.username) + "\n" + \
					"user_firstlastname:" + str(user.first_name) + " " + str(user.last_name) + "\n" + \
					"___INFO CHAT___\n" + \
					"chat_id:" 			+ str(chat.id) + "\n" + \
					"chat_type:" 			+ str(chat.type)+"\n" + "chat_title:" + str(chat.title) + "\n" + \
					"___TESTO___\n" + \
					"text:" 				+ str(text) + "\n" + \
					"date:" 				+ str(date) + \
					"\n_____________\n"

		log_tmp = open("logs/logs.txt","a+")
		log_tmp.write("\n"+message)
	except:
		pass


def main():
	updater = Updater(TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
	dp = updater.dispatcher
	dp.add_handler(MessageHandler(Filters.all, logging_message),1)

	#Easter Egg
	dp.add_handler(CommandHandler('smonta_portoni',smonta_portoni))
	dp.add_handler(CommandHandler('santino',santino))
	dp.add_handler(CommandHandler('prof_sticker' ,prof_sticker))
	dp.add_handler(MessageHandler(Filters.regex('/lezioni cazzeggio'), bladrim))
	dp.add_handler(CommandHandler('leiCheNePensaSignorina',lei_che_ne_pensa_signorina))

	#Informative command
	dp.add_handler(CommandHandler('sdidattica', informative_callback))
	dp.add_handler(CommandHandler('sstudenti', informative_callback))
	dp.add_handler(CommandHandler('cea', informative_callback))
	dp.add_handler(CommandHandler('ersu', informative_callback))
	dp.add_handler(CommandHandler('ufficioersu', informative_callback))
	dp.add_handler(CommandHandler('urp', informative_callback))
	dp.add_handler(CommandHandler('biblioteca', informative_callback))
	dp.add_handler(CommandHandler('gruppi', informative_callback))
	dp.add_handler(CommandHandler('cus', informative_callback))

	dp.add_handler(CommandHandler('lezioni', lezioni))
	dp.add_handler(CommandHandler('esami',esami))

	dp.add_handler(CommandHandler('prof', prof))

	dp.add_handler(CommandHandler('aulario', aulario))
	dp.add_handler(MessageHandler(Filters.regex(AULARIO), aulario))
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(MessageHandler(Filters.regex(HELP), help))
	dp.add_handler(CommandHandler('contributors', informative_callback))

	dp.add_handler(CommandHandler('rappresentanti', informative_callback))
	dp.add_handler(CommandHandler('rappresentanti_dmi', informative_callback))
	dp.add_handler(CommandHandler('rappresentanti_informatica', informative_callback))
	dp.add_handler(CommandHandler('rappresentanti_matematica', informative_callback))
	dp.add_handler(CommandHandler('report', report))
	dp.add_handler(CommandHandler('chatid',give_chat_id))
	dp.add_handler(CommandHandler('send_log', send_log))
	dp.add_handler(CommandHandler('send_chat_ids', send_chat_ids))
	dp.add_handler(CommandHandler('errors', send_errors))
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('cloud', informative_callback))
	dp.add_handler(MessageHandler(Filters.regex(CLOUD), informative_callback))
	dp.add_handler(MessageHandler(Filters.regex(SEGNALAZIONE), informative_callback))

  # generic buttons
	dp.add_handler(CallbackQueryHandler(generic_button_handler,        pattern='^(exit_cmd)'))
	dp.add_handler(CallbackQueryHandler(submenu_handler,               pattern='sm_.*'))
	dp.add_handler(CallbackQueryHandler(md_handler,                    pattern='md_.*'))
	dp.add_handler(CallbackQueryHandler(submenu_with_args_handler,     pattern='sm&.*'))
	dp.add_handler(CallbackQueryHandler(none_handler,                  pattern='NONE'))

  # aulario and calendar
	dp.add_handler(CallbackQueryHandler(calendar_handler,       pattern='cal_.*'))
	dp.add_handler(CallbackQueryHandler(month_handler,          pattern='m_[np]_.*'))
	dp.add_handler(CallbackQueryHandler(subjects_handler,       pattern='sb_.*'))
	dp.add_handler(CallbackQueryHandler(subjects_arrow_handler, pattern='pg_.*'))

  # drive & gitlab buttons
	dp.add_handler(CallbackQueryHandler(callback,               pattern='Drive_.*'))
	dp.add_handler(CallbackQueryHandler(gitlab_handler,         pattern='git_.*'))

	# regolamento didattico
	dp.add_handler(CommandHandler('regolamentodidattico', regolamentodidattico))
	dp.add_handler(CallbackQueryHandler(triennale,                   pattern='reg_triennale_button'))
	dp.add_handler(CallbackQueryHandler(magistrale,                  pattern='reg_magistrale_button'))
	dp.add_handler(CallbackQueryHandler(regdid,                      pattern='regdid_button'))
	dp.add_handler(CallbackQueryHandler(regolamenti,                 pattern='Regolamento*'))
	dp.add_handler(CallbackQueryHandler(regolamentodidattico_button, pattern='regolamentodidattico_button'))

	# esami
	dp.add_handler(MessageHandler(Filters.regex(r"^(?!=<[/])[Ii]ns:\s+"), esami_input_insegnamento)) #regex accetta [/ins: nome] oppure [/Ins: nome], per agevolare chi usa il cellulare
	dp.add_handler(CallbackQueryHandler(esami_handler, pattern='esami_button_.*'))

	# lezioni
	dp.add_handler(CallbackQueryHandler(lezioni_handler, pattern='lezioni_button_*'))
	dp.add_handler(MessageHandler(Filters.regex(r"^(?!=<[/])[Nn]ome:\s+"), lezioni_input_insegnamento))

	# job queue
	j = updater.job_queue

	j.run_repeating(updater_lep, interval=86400, first=0) 				# job_updater_lep (24h)
	j.run_daily(updater_schedule, time = time(hour = 1, minute = 5) )       # you need to put 1 hour late cause of the timezone
	if (config_map['debug']['disable_drive'] == 0):
		dp.add_handler(CommandHandler('drive',drive))

	if config_map['debug']['disable_gitlab'] == 0:
		dp.add_handler(CommandHandler('git', git))
		dp.add_handler(CommandHandler('gitlab', git))

	if	config_map['debug']['disable_drive'] == 0 or \
		config_map['debug']['disable_gitlab'] == 0:
			dp.add_handler(MessageHandler(Filters.regex('/request'), request))
			dp.add_handler(MessageHandler(Filters.regex('/add_db'), add_db))

	if (config_map['debug']['disable_db'] == 0):
		dp.add_handler(CommandHandler('stats',stats))
		dp.add_handler(CommandHandler('stats_tot',stats_tot))

	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
    main()
