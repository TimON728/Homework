import telebot
import threading
import time
import os

foto = ''
stop_spam = False


def spam(photo, message):
    while not stop_spam:
        bot.send_photo(message.chat.id, photo)
        time.sleep(0.05)


def def_stop_spam():
    global stop_spam
    stop_spam = True


bot = telebot.TeleBot(os.environ.get('TOKEN_FOR_KIRILL'))


@bot.message_handler(commands=['adv'])
def adv(message):
    global stop_spam
    stop_spam = True
    bot.send_message(message.chat.id, 'Ладно')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    global stop_spam
    bot.send_message(message.chat.id, 'ща')
    stop_spam = False
    while True:
        spam(foto, message)
        time.sleep(0.05)



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