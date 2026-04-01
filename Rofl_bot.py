import telebot
import threading
import time
import os

foto = ''
chat = ''
stop_spam = False


def spam(photo):
    global chat
    while not stop_spam:
        bot.send_photo(chat, photo)
        time.sleep(0.5)


def def_stop_spam():
    global stop_spam
    stop_spam = True


bot = telebot.TeleBot(os.environ.get('TOKEN_FOR_KIRILL'))


@bot.message_handler(commands=['adv'])
def adv(message):
    global stop_spam
    stop_spam = True


@bot.message_handler(commands=['start'])
def send_welcome(message):
    global chat, stop_spam
    if '@' in message.text:
        bot.send_message(message.chat.id, 'ща')
        txt = message.text.split()[1]
        bot.send_message(message.chat.id, 'ща0.5')
        try:
            chat = bot.get_chat(txt)
            bot.send_message(message.chat.id, 'ща1')
        except Exception as e:
            bot.send_message(message.chat.id, f'Не могу найти {txt}: {e}')
            return
        bot.send_message(message.chat.id, 'ща1')
        stop_spam = False
        spam(foto)
        timer = threading.Timer(60.0, def_stop_spam)
        timer.start()
    else:
        bot.send_message(message.chat.id, 'Отказано')



@bot.message_handler(content_types=['photo'])
def send_photo(message):
    global foto
    foto =  message.photo[-1].file_id
    bot.send_message(message.chat.id, 'фото принято')

while True:
    try:
        bot.polling(none_stop=True, interval=0)
        # если возникла ошибка — сообщаем про исключение и продолжаем работу
    except Exception as e:
        print(f'❌❌❌❌❌ Сработало исключение! ❌❌❌❌❌')