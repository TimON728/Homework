import telebot

foto = ''

bot = telebot.TeleBot("8544707194:AAFEC_CsO0XQOoywEC2cIS7hciWklWUU59Q")
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if '@' in message.text:
        bot.send_message(message.chat.id, 'ща')
        txt = message.text.split()[1]
        chat = bot.get_chat(txt)
        bot.send_message(message.chat.id, 'ща1')
        while True:
            bot.send_photo(chat.id, foto)
    else:
        bot.send_message(message.chat.id, 'Иди нахуй')


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