import telebot
from telebot import types
import sqlite3
from datetime import datetime
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

bot = telebot.TeleBot(os.environ.get('TOKEN'))

conn = sqlite3.connect('homework.db', check_same_thread=False)  # файл базы данных
cursor = conn.cursor()
users = {}

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, school_class TEXT)''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, subject TEXT, task TEXT, time INTEGER, photo_id TEXT, UNIQUE(school_class, subject))''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS timetable (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, timetable TEXT, time INTEGER, UNIQUE(school_class, timetable))''')

conn.commit()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    global users
    user_id = message.from_user.id
    cursor.execute('''SELECT id, school_class FROM schools WHERE user_id = ?''', (user_id,))
    row = cursor.fetchone()
    if row:
        users[user_id] = {'school': row[1], 'reg': True}
        bot.send_message(message.from_user.id,
                         f"Привет! Напомню команды:\n /hw - посмотреть дз\n /new_hw - добавить дз\n /tt - помсотреть рассписание \n /new_tt - изменить рассписание \nЕсли сменил школу, то просто введи /school")
    else:
        bot.send_message(message.from_user.id,
                         "Привет! Это бот для хранения домашнего задания. Для начала работы бота введи название своей школы и свой класс через команду /school")


@bot.message_handler(commands=['school'])
def reg_school(message):
    user_id = message.from_user.id
    bot.send_message(message.from_user.id, "Введи название школы и класс, на пример: 'Лодейнопольская СОШ №3, 8а'")
    users[user_id] = {'condition': 'wait school'}


@bot.message_handler(commands=['new_hw', 'hw'])
def new_hm(message):
    global users
    user_id = message.from_user.id
    if user_id in users and users[user_id]['reg'] == True:
        if message.text == "/hw":
            hw_item = []
            hw_chel = []
            hw_foto = []
            hw_time = []
            hw_list = []
            cursor.execute('''
            SELECT subject, task, time, photo_id FROM homework WHERE school_class = ?
            ''', (users[user_id]['school'],))
            rows = cursor.fetchall()
            if len(rows) > 0:
                for subject, task, time, photo_id in rows:
                    hw_item.append(subject)
                    hw_chel.append(task)
                    hw_time.append(time)
                    hw_foto.append(photo_id)
                for i in range(len(hw_item)):
                    if hw_chel[i] == 'chek in photo_id':
                        bot.send_photo(message.from_user.id, photo=hw_foto[i], caption=f"{hw_item[i]} (обн. {hw_time[i]})")
                    else:
                        hw_list.append(f'{hw_item[i]}: {hw_chel[i]} (обн. {hw_time[i]})')
                bot.send_message(message.from_user.id, f'{f'\n'.join(hw_list)}')
            else:
                bot.send_message(message.from_user.id, "Задания ещё не добавили")
        elif message.text == '/new_hw':
            bot.send_message(message.from_user.id,
                             "Введи предмет и задание. Например: 'Алгебра: №67' (Вводи строго один предмет!). "
                             "Если хочешь добавить фото, то напиши так: 'Химия: фото', а потом отправь само фото")
            users[user_id]['condition'] = 'wait new hw'
    else:
        bot.send_message(message.from_user.id, 'Сначала пройди регистрацию через команду /start')


@bot.message_handler(commands=['tt', 'new_tt'])
def timetable(message):
    global users
    user_id = message.from_user.id
    if user_id in users and users[user_id]['reg'] == True:
        if message.text == '/tt':
            tt = ''
            ttt = ''
            cursor.execute('''
                        SELECT timetable, time FROM timetable WHERE school_class = ?
                        ''', (users[user_id]['school'],))
            rows = cursor.fetchall()
            if len(rows) > 0:
                for timetable, time in rows:
                    tt = timetable
                    ttt = time
                bot.send_photo(message.from_user.id, caption=f'Расписание на завтра (обн. {ttt})', photo=tt)
            else:
                bot.send_message(message.from_user.id, 'Рассписание не добавили')
        elif message.text == '/new_tt':
            bot.send_message(message.from_user.id, 'Жду фото рассписания')
            users[user_id]['condition'] = 'wait new tt'
    else:
        bot.send_message(message.from_user.id, 'Сначал пройди регестрацию через команду /start')


@bot.message_handler(content_types=['text', 'photo'])
def send_school(message):
    global users
    user_id = message.from_user.id
    if users[user_id]['condition'] == 'wait school':
        users[user_id] = {'school': message.text, 'reg': False, 'condition': 'wait school'}
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_message(message.from_user.id, text=f'Твоя школа и класс - "{users[user_id]['school']}"?',
                         reply_markup=keyboard)
    elif users[user_id]['condition'] == 'wait new hw':
        print("Текст сообщения:", repr(message.text))
        print("Есть 'фото'?", 'фото' in message.text.lower())
        if 'фото' in message.text.lower():
            users[user_id]['item'] = list(map(str, message.text.split(': ')))
            users[user_id]['item'] = users[user_id]['item'][0]
            users[user_id]['condition'] = 'wait photo'
            bot.send_message(message.from_user.id, 'Теперь жду фотку')
        else:
            try:
                users[user_id]['item'], users[user_id]['chel'] = map(str, message.text.split(': '))
                keyboard = types.InlineKeyboardMarkup()
                key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
                keyboard.add(key_yes)
                key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
                keyboard.add(key_no)
                bot.send_message(message.from_user.id, text=f'Дз - "{users[user_id]['item']}: {users[user_id]['chel']}"?', reply_markup=keyboard)
            except:
                bot.send_message(message.from_user.id,
                                 'Ты чуть бота не сломал. Без шуток. Вводи только один предмет за раз. И только по шаблону "Предмет: домашка"')
    elif users[user_id]['condition'] == 'wait photo':
        users[user_id]['chel'] = message.photo[-1].file_id
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_photo(message.from_user.id, caption=f'{users[user_id]['item']}?', photo=users[user_id]['chel'], reply_markup=keyboard)
    elif users[user_id]['condition'] == 'wait new tt':
        users[user_id]['tt'] = message.photo[-1].file_id
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_photo(message.from_user.id, caption=f'Рассписание на завтра?', photo=users[user_id]['tt'], reply_markup=keyboard)



@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global users
    user_id = call.from_user.id
    if users[user_id]['condition'] == 'wait school':
        if call.data == "yes":
            bot.send_message(call.message.chat.id,
                             'Хорошо. Теперь ты можешь посмотреть дз (/hw) или ввести новое(/new_hw). Ещё тф можешь посмотреть рассписание (/tt) ли обновить (/new_tt)')
            cursor.execute('''
                       INSERT INTO schools (user_id, school_class)
                       VALUES (?, ?)
                       ''', (user_id, users[user_id]['school']))
            conn.commit()
            users[user_id]['condition'] = ''
            users[user_id]['reg'] = True
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /school')
    elif users[user_id]['condition'] == 'wait new hw':
        if call.data == "yes":
            now = datetime.now().strftime('%d.%m в %H:%M')
            cursor.execute('''
            INSERT OR REPLACE INTO homework (school_class, subject, task, time)
            VALUES (?, ?, ?, ?)
            ''', (users[user_id]['school'], users[user_id]['item'], users[user_id]['chel'], now))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Если хочешь ввести ещё дз, то используй команду /new_hw ещё раз')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_hw')
    elif users[user_id]['condition'] == 'wait photo':
        if call.data == "yes":
            now = datetime.now().strftime('%d.%m в %H:%M')
            cursor.execute('''
            INSERT OR REPLACE INTO homework (school_class, subject, task, time, photo_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (users[user_id]['school'], users[user_id]['item'], 'chek in photo_id', now, users[user_id]['chel']))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Если хочешь ввести ещё дз, то используй команду /new_hw ещё раз')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_hw')
    elif users[user_id]['condition'] == 'wait new tt':
        if call.data == "yes":
            now = datetime.now().strftime('%d.%m в %H:%M')
            cursor.execute('''
            INSERT OR REPLACE INTO timetable (school_class, timetable, time)
            VALUES (?, ?, ?)
            ''', (users[user_id]['school'], users[user_id]['tt'], now))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Если хочешь обновить рассписание, то используй команду /new_tt ещё раз')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_tt')


keep_alive()
while True:
    try:
        bot.polling(none_stop=True, interval=0)
        # если возникла ошибка — сообщаем про исключение и продолжаем работу
    except Exception as e:
        now = datetime.now().strftime('%d.%m в %H:%M:%S')
        print(f'❌❌❌❌❌ Сработало исключение! ❌❌❌❌❌ {now}')
