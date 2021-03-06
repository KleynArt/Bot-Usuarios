#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from typing import Optional
from mcstatus import MinecraftServer
import telegram
from telegram.update import Update
from telegram.ext import CallbackContext, CommandHandler, JobQueue, Job, Updater
from socket import timeout


@dataclass
class CheckTask:
    username: str
    host: str
    port: int
    chat_id: int
    msg_id: int
    status: str
    job: Optional[Job]


# PAST YOUR TOKEN HERE
BOT_TOKEN = "2092822230:AAFtBXRgDO72TtMxUEPCklD6KQ-cygAil0c"
if not len(BOT_TOKEN):
    BOT_TOKEN = sys.argv[1]
    
bot = telegram.Bot(BOT_TOKEN)
updater = Updater(BOT_TOKEN, use_context=True)
tasks = {}
serverip = ("\n\nGeek Cubans+ Network \n\nâ„¹ï¸IP: play.geekcubans.nat.cu")

############################################################################################################

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hola! soy el bot para mantenerte informado.\n"
        "de los usuarios conectados en Geek Cubans+ Network\n" 
        , parse_mode = "Markdown")


def check(context):
    task = context.job.context
    try:
        status = MinecraftServer(task.host, task.port).status()
        name = "ðŸŒUsuarios Conectados"
        # Try get server name(first string of motd)
        try:
            for pair in status.description["extra"]:
                name += pair["text"]
            name = name.split("\n")[0].strip()
        except:
            pass
        if len(name) > 60 or len(name) < 1:
            name = "â‡ï¸ACTIVO"
        online = ""
        # Try get players name
        try:
            online = ", ".join(sorted([i.name for i in status.players.sample]))
        except:
            pass
        if len(online) > 60 or len(online) < 1:
            online = str(status.players.online)
        new_text = name + ": " + online + serverip
    except Exception as e:
        new_text = "âš ï¸NETWORK EN MANTENIMIENTO"

    # To skip telegram exception "Message is not modified"
    if task.status != new_text:
        try:
            bot.edit_message_text(new_text, task.chat_id, task.msg_id)
            task.status = new_text
        except Exception as e:
            task.job.schedule_removal()
            print(task.host + ' checker removed')
            del tasks[task.chat_id]
    # Save tasks
    file = open("tasks.txt", "w")
    for task in tasks.values():
        file.write(task.username + ',')
        file.write(task.host + ',')
        file.write(str(task.port) + ',')
        file.write(str(task.chat_id) + ',')
        file.write(str(task.msg_id) + ",")
        file.write(task.status.replace("\n", ""))
        file.write('\n')
    file.close()



def check_cmd(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    try:
        tmp = context.args[0].split(':')
        host = str(tmp[0])
        if len(tmp) > 1:
            port = int(tmp[1])
        else:
            port = 25565
        MinecraftServer(host, port).status()
    except (IndexError, ValueError):
        try:
            update.message.reply_text("Correct usage:\n/check host\n/check host:port")
        except:
            pass
        return
    except Exception as e:
        update.message.reply_text("Error: {}".format(e))
        return

    # Add job to queue and stop current one if there is a timer already
    if chat_id in tasks:
        task = tasks[chat_id]
        bot.edit_message_text("Stopped. Last " + task.status, task.chat_id, task.msg_id)
        task.job.schedule_removal()
    print(username, host, port)
    msg_id = update.message.reply_text("Started", disable_notification=True).message_id
    task = CheckTask(username, host, port, chat_id, msg_id, "", None)
    tasks[chat_id] = task

    # First try in 1th second. Then check every 20 seconds
    task.job = context.job_queue.run_repeating(check, 20, 1, context=task)


def stop(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id in tasks:
        task = tasks[chat_id]
        task.job.schedule_removal()
        bot.edit_message_text("Stopped. Last " + task.status, task.chat_id, task.msg_id)
        del tasks[chat_id]
    else:
        update.message.reply_text("Nothing to stop")

############################################################################################################

# Load tasks
try:
    file = open("tasks.txt", "r")
    for line in file.readlines():
        print(line)
        tmp = line.replace("\n", "").split(',')
        task = CheckTask(tmp[0], tmp[1], int(tmp[2]), int(tmp[3]), int(tmp[4]), ",".join(tmp[5:]), None)
        task.job = updater.job_queue.run_repeating(check, 20, 1, context=task)
        tasks[task.chat_id] = task
    file.close()
except IOError:
    pass

# Get the dispatcher to register handlers
dp = updater.dispatcher
dp.add_handler(CommandHandler("check", check_cmd, pass_args=True, pass_job_queue=True,pass_chat_data=True))
dp.add_handler(CommandHandler("stop", stop))
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", start))

# Start the Bot
updater.start_polling()
# Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
# SIGABRT. This should be used most of the time, since start_polling() is
# non-blocking and will stop the bot gracefully.
updater.idle()
