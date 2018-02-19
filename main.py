# -*- coding: utf-8 -*-
from functions import *
reload(sys)
sys.setdefaultencoding('utf8')

bot= telegram.Bot(TOKEN)

with open('config/settings.yaml') as yaml_config:
	config_map = yaml.load(yaml_config)

def record_everything(bot, update):
	message = str(update.message)
	log_tmp = open("logs/logs.txt","a+")
	log_tmp.write("\n"+message)

def main():
	updater = Updater(TOKEN)
	dp = updater.dispatcher
	dp.add_handler(MessageHandler(Filters.all, record_everything),1)
	dp.add_handler(CallbackQueryHandler(button_handler))

  	#Easter Egg
	dp.add_handler(CommandHandler('smonta_portoni',smonta_portoni))
	dp.add_handler(CommandHandler('santino',santino))
	dp.add_handler(CommandHandler('prof_sticker' ,prof_sticker))
	dp.add_handler(RegexHandler('/lezioni cazzeggio',bladrim))
	dp.add_handler(CommandHandler('leiCheNePensaSignorina',lei_che_ne_pensa_signorina))
	# dp.add_handler(RegexHandler('/forum',forum_bot))

  	#Informative command
	dp.add_handler(CommandHandler('sdidattica', lambda bot, update: informative_callback(bot, update, 'sdidattica')))
	dp.add_handler(CommandHandler('sstudenti', lambda bot, update: informative_callback(bot, update, 'sstudenti')))
	dp.add_handler(CommandHandler('cea', lambda bot, update: informative_callback(bot, update, 'cea')))
	dp.add_handler(CommandHandler('ersu', lambda bot, update: informative_callback(bot, update, 'ersu')))
	dp.add_handler(CommandHandler('ufficioersu', lambda bot, update: informative_callback(bot, update, 'ufficioersu')))
	dp.add_handler(CommandHandler('urp', lambda bot, update: informative_callback(bot, update, 'urp')))
	dp.add_handler(CommandHandler('mensa', mensa))
	dp.add_handler(CommandHandler('biblioteca', lambda bot, update: informative_callback(bot, update, 'biblioteca')))
	dp.add_handler(CommandHandler('cus', lambda bot, update: informative_callback(bot, update, 'cus')))

	dp.add_handler(CommandHandler('lezioni', lambda bot, update, args: lezioni(bot, update, args), pass_args=True))
	dp.add_handler(CommandHandler('esami', lambda bot, update, args: esami(bot, update, args), pass_args=True))

	dp.add_handler(CommandHandler('mlezioni', lambda bot, update, args: lezioni(bot, update, args, True), pass_args=True))
	dp.add_handler(CommandHandler('mesami', lambda bot, update, args: esami(bot, update, args, True), pass_args=True))

	dp.add_handler(CommandHandler('prof', prof, pass_args=True))

	dp.add_handler(CommandHandler('aulario', lambda bot, update: informative_callback(bot, update, 'aulario')))
	dp.add_handler(CommandHandler('help',help))
	dp.add_handler(CommandHandler('contributors', lambda bot, update: informative_callback(bot, update, 'contributors')))

	dp.add_handler(CommandHandler('rappresentanti', lambda bot, update: informative_callback(bot, update, 'rappresentanti')))
	dp.add_handler(CommandHandler('rappresentanti_dmi', lambda bot, update: informative_callback(bot, update, 'rappresentanti_dmi')))
	dp.add_handler(CommandHandler('rappresentanti_informatica', lambda bot, update: informative_callback(bot, update, 'rappresentanti_informatica')))
	dp.add_handler(CommandHandler('rappresentanti_matematica', lambda bot, update: informative_callback(bot, update, 'rappresentanti_matematica')))
	dp.add_handler(CommandHandler('chatid',giveChatId))
	dp.add_handler(CommandHandler('sendlog', sendLog))
	dp.add_handler(CommandHandler('sendChatids', sendChatIds))
	dp.add_handler(CommandHandler('errors', sendErrors))
	dp.add_handler(CommandHandler('start', start))

	#JobQueue
	j = updater.job_queue

	job_dmi_news = j.run_repeating(avviso, interval=60)
	job_updater_esami = j.run_repeating(update_esami, interval=86400, first=0) #24h


	if (config_map['debug']['disable_drive'] == 0):
	  dp.add_handler(CommandHandler('drive',drive))
	  dp.add_handler(RegexHandler('/adddb',adddb))
	  dp.add_handler(RegexHandler('/request',request))

	if (config_map['debug']['disable_db'] == 0):
	  dp.add_handler(CommandHandler('stats',stats))
	  dp.add_handler(CommandHandler('stats_tot',statsTot))

	if (config_map['debug']['disable_chatid_logs'] == 0):
	  dp.add_handler(RegexHandler('/news',news_))
	  dp.add_handler(CommandHandler('spamnews',spamnews))
	  dp.add_handler(CommandHandler('disablenews',disablenews))
	  dp.add_handler(CommandHandler('enablenews',enablenews))


	dp.add_handler(CallbackQueryHandler(callback))
	
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
    main()
