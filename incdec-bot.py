from telegram import MessageEntity
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from collections import defaultdict
from rotate_word import rotate_word

import os
import sys
import logging
import json
from custom_filters import IncDecFilter

def start(bot, update):
    update.message.reply_text('Hello World!')

"""
Replies with a rotated meme string, courtesy of @inityx, of the message
which trigger this handler.
"""
def rotate(bot, update):
    reply_string = "```\n"
    reply_string += rotate_word(update.message.text.replace("/rotate ", ""))
    reply_string += "```"
    update.message.reply_text(reply_string, parse_mode=ParseMode.MARKDOWN)

"""
Replies with the score of the user whom'st'dve triggers this handler.
"""
def myscore(bot, update):
    username = update.message.from_user.username
    score = db[username]
    update.message.reply_text(
            'Hello {}, your score is {}.'.format(username, score))

"""
Replies with the score of all the mentioned targets in the message text.
"""
def score(bot, update):
    mentioned_users = set()
    for mention in update.message.entities:
        if mention.type != 'mention':
            continue
        mention_begin = mention.offset
        mention_end = mention_begin + mention.length

        username = update.message.text[mention_begin+1:mention_end]
        mentioned_users.add(username)

    reply_str = ''
    for user in mentioned_users:
        reply_str += '{} has a score of {}.\n'.format(user, db[user])
    update.message.reply_text(reply_str)

"""
Updates the score of all mentioned targets based off the action string
immediately following the mention.
"""
def update_score(bot, update):
    mentioned_users = set()
    for mention in update.message.entities:
        mention_begin = mention.offset
        mention_end = mention_begin + mention.length

        username = update.message.text[mention_begin+1:mention_end]

        # Prevent users from modifying their own score
        if username == update.message.from_user.username:
            continue

        # Extract the action from the message
        action = update.message.text[mention_end:].strip()[:2]

        if '--' in action or '—' in action:
            db[username] -= 1
            mentioned_users.add(username)
        elif '++' in action:
            db[username] += 1
            mentioned_users.add(username)

    with open('incdec-bot-db.json', 'w') as dbfile:
        json.dump(db, dbfile)

    reply_str = ''
    for user in mentioned_users:
        reply_str += '{} now has a score of {}.\n'.format(user, db[user])
    update.message.reply_text(reply_str)


# MAIN PROGRAM
if "TELEGRAM_BOT_API_KEY" in os.environ:
    updater = Updater(os.environ.get("TELEGRAM_BOT_API_KEY"))
else:
    sys.exit("Telegram Bot API key not in TELEGRAM_BOT_API_KEY environment variable")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

custom_filter = IncDecFilter()
total_filter = (Filters.text & Filters.entity(MessageEntity.MENTION) & custom_filter)

updater.dispatcher.add_handler(MessageHandler(total_filter, update_score))
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('rotate', rotate))
updater.dispatcher.add_handler(CommandHandler('score', score))
updater.dispatcher.add_handler(CommandHandler('myscore', myscore))

dbstr = open('incdec-bot-db.json', 'r').read()
db_raw = json.loads(dbstr)
db = defaultdict(int, db_raw)

updater.start_polling()
updater.idle()
