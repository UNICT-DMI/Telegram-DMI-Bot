# -*- coding: utf-8 -*-
"""Main module"""
from telegram import BotCommand
from telegram.ext import CallbackQueryHandler, CommandHandler, Dispatcher, Filters, MessageHandler, Updater

from module.commands.aulario import aulario, calendar_handler, month_handler, subjects_arrow_handler, subjects_handler
from module.callback_handlers import exit_handler, informative_callback, md_handler, none_handler, submenu_handler
from module.commands.esami import esami, esami_handler, esami_input_insegnamento
from module.commands.lezioni import lezioni, lezioni_handler, lezioni_input_insegnamento
from module.commands.professori import prof
from module.commands.start import start
from module.commands.stats import stats, stats_tot
from module.commands.help import help_cmd
from module.commands.report import report
from module.commands.request import add_db, request, request_handler
from module.commands.gdrive import drive, drive_handler
from module.commands.regolamento_didattico import regolamentodidattico, regolamentodidattico_handler, send_regolamento
from module.easter_egg_func import bladrim, lei_che_ne_pensa_signorina, prof_sticker, santino, smonta_portoni
from module.gitlab import git, gitlab_handler
from module.job_updater import updater_lep
from module.shared import AULARIO, CLOUD, HELP, SEGNALAZIONE, config_map
from module.utils.send_utils import send_chat_ids, send_errors, send_log
from module.debug import error_handler, log_message


def add_commands(up: Updater):
    """Adds the list of commands with their description to the bot

    Args:
        up (Updater): supplyed Updater
    """
    #TODO: add all commands and remove the comment in the main
    commands = [
        BotCommand("start", "messaggio di benvenuto"),
        BotCommand("help ", "help"),
        BotCommand("esami", "cerca informazioni sugli esami"),
        BotCommand("lezioni", "cerca informazioni sulle lezioni"),
    ]
    up.bot.set_my_commands(commands=commands)


def add_handlers(dp: Dispatcher):
    """Adds all the handlers the bot will react to

    Args:
        dp (:class:`Dispatcher`): supplyed Dispatcher
    """
    dp.add_error_handler(error_handler)
    dp.add_handler(MessageHandler(Filters.all, log_message), 1)

    #Easter Egg
    dp.add_handler(CommandHandler('smonta_portoni', smonta_portoni))
    dp.add_handler(CommandHandler('santino', santino))
    dp.add_handler(CommandHandler('prof_sticker', prof_sticker))
    dp.add_handler(MessageHandler(Filters.regex('/lezioni cazzeggio'), bladrim))
    dp.add_handler(CommandHandler('leiCheNePensaSignorina', lei_che_ne_pensa_signorina))

    #Informative command
    dp.add_handler(CommandHandler('sdidattica', informative_callback))
    dp.add_handler(CommandHandler('studenti', informative_callback))
    dp.add_handler(CommandHandler('cea', informative_callback))
    dp.add_handler(CommandHandler('ersu', informative_callback))
    dp.add_handler(CommandHandler('ufficioersu', informative_callback))
    dp.add_handler(CommandHandler('urp', informative_callback))
    dp.add_handler(CommandHandler('biblioteca', informative_callback))
    dp.add_handler(CommandHandler('gruppi', informative_callback))
    dp.add_handler(CommandHandler('cus', informative_callback))

    dp.add_handler(CommandHandler('lezioni', lezioni))
    dp.add_handler(CommandHandler('esami', esami))

    dp.add_handler(CommandHandler('prof', prof))

    dp.add_handler(CommandHandler('aulario', aulario))
    dp.add_handler(MessageHandler(Filters.regex(AULARIO), aulario))
    dp.add_handler(CommandHandler('help', help_cmd))
    dp.add_handler(MessageHandler(Filters.regex(HELP), help_cmd))
    dp.add_handler(CommandHandler('contributors', informative_callback))

    dp.add_handler(CommandHandler('rappresentanti', informative_callback))
    dp.add_handler(CommandHandler('rappresentanti_dmi', informative_callback))
    dp.add_handler(CommandHandler('rappresentanti_informatica', informative_callback))
    dp.add_handler(CommandHandler('rappresentanti_matematica', informative_callback))
    dp.add_handler(CommandHandler('report', report))
    dp.add_handler(CommandHandler('chatid', lambda u, c: u.message.reply_text(u.message.chat_id)))
    dp.add_handler(CommandHandler('send_log', send_log))
    dp.add_handler(CommandHandler('send_chat_ids', send_chat_ids))
    dp.add_handler(CommandHandler('errors', send_errors))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('cloud', informative_callback))
    dp.add_handler(MessageHandler(Filters.regex(CLOUD), informative_callback))
    dp.add_handler(MessageHandler(Filters.regex(SEGNALAZIONE), informative_callback))

    # generic buttons
    dp.add_handler(CallbackQueryHandler(exit_handler, pattern='^(exit_cmd)'))
    dp.add_handler(CallbackQueryHandler(submenu_handler, pattern='sm_.*'))
    dp.add_handler(CallbackQueryHandler(md_handler, pattern='md_.*'))
    dp.add_handler(CallbackQueryHandler(none_handler, pattern='NONE'))

    # aulario and calendar
    dp.add_handler(CallbackQueryHandler(calendar_handler, pattern='cal_.*'))
    dp.add_handler(CallbackQueryHandler(month_handler, pattern='m_[np]_.*'))
    dp.add_handler(CallbackQueryHandler(subjects_handler, pattern='sb_.*'))
    dp.add_handler(CallbackQueryHandler(subjects_arrow_handler, pattern='pg_.*'))

    # drive & gitlab buttons
    dp.add_handler(CallbackQueryHandler(drive_handler, pattern=r'^drive_file_.*'))
    dp.add_handler(CallbackQueryHandler(request_handler, pattern=r'^drive_accept_.*'))
    dp.add_handler(CallbackQueryHandler(gitlab_handler, pattern='git_.*'))

    # regolamento didattico
    dp.add_handler(CommandHandler('regolamentodidattico', regolamentodidattico))
    dp.add_handler(CallbackQueryHandler(regolamentodidattico_handler, pattern=r'^reg_button_.*'))
    dp.add_handler(CallbackQueryHandler(send_regolamento, pattern=r'^Regolamento Didattico.*'))

    # esami
    #regex accetta [/ins: nome] oppure [/Ins: nome], per agevolare chi usa il cellulare
    dp.add_handler(CallbackQueryHandler(esami_handler, pattern='esami_button_.*'))
    dp.add_handler(MessageHandler(Filters.regex(r"^(?!=<[/])[Ii]ns:\s+"), esami_input_insegnamento))

    # lezioni
    dp.add_handler(CallbackQueryHandler(lezioni_handler, pattern='lezioni_button_*'))
    dp.add_handler(MessageHandler(Filters.regex(r"^(?!=<[/])[Nn]ome:\s+"), lezioni_input_insegnamento))

    # drive and gitlab commands
    if config_map['debug']['disable_drive'] == 0:
        dp.add_handler(CommandHandler('drive', drive))

    if config_map['debug']['disable_gitlab'] == 0:
        dp.add_handler(CommandHandler('git', git))
        dp.add_handler(CommandHandler('gitlab', git))

    if config_map['debug']['disable_drive'] == 0 or \
     config_map['debug']['disable_gitlab'] == 0:
        dp.add_handler(CommandHandler('request', request))
        dp.add_handler(CommandHandler('add_db', add_db))

    # stats command
    if config_map['debug']['disable_db'] == 0:
        dp.add_handler(CommandHandler('stats', stats))
        dp.add_handler(CommandHandler('stats_tot', stats_tot))


def add_jobs(dp: Dispatcher):
    """Schedule the jobs in the JobQueue

    Args:
        job_queue (:class:`JobQueue`): job queue
    """
    dp.job_queue.run_repeating(updater_lep, interval=86400, first=1)  # job_updater_lep (24h)


def main():
    """Main function"""
    updater = Updater(config_map['token'], request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    #add_commands(updater)
    add_handlers(updater.dispatcher)
    add_jobs(updater.dispatcher)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
