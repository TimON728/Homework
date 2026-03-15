import telebot
from telebot import types
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
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
MY_ID = int(os.environ.get('MY_ID', 0))

conn = sqlite3.connect('homework.db', check_same_thread=False)  # файл базы данных
cursor = conn.cursor()
users = {}
user_timers = {}

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, school_class TEXT)''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, subject TEXT, task TEXT, time INTEGER, photo_id TEXT, UNIQUE(school_class, subject))''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS homework_photo (id INTEGER PRIMARY KEY, homework_id INTEGER, photo_id TEXT, FOREIGN KEY (homework_id) REFERENCES homework(id))''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS timetable (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, timetable TEXT, time INTEGER, UNIQUE(school_class, timetable))''')

conn.commit()


def rework(school):
    school = school.lower()
    school = school.strip(f'"\' ')
    school = school.replace(' ', '')
    return school


def send_question(message):
    global users
    user_id = message
    media_group = []
    for i, cap in enumerate(users[user_id]['hw_foto']):
        if i == 0:
            if users[user_id]['hw_chel'] != 'Don`t send' or users[user_id]['hw_chel'] != 'chek in photo_id':
                media_group.append(types.InputMediaPhoto(cap, caption=f'{users[user_id]['hw_chel']}'))
            else:
                media_group.append(types.InputMediaPhoto(cap))
        else:
            media_group.append(types.InputMediaPhoto(cap))
    bot.send_media_group(user_id, media=media_group)
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
    keyboard.add(key_no)
    bot.send_message(user_id, text=f'{users[user_id]['hw_item']}?',
                     reply_markup=keyboard)


@bot.message_handler(commands=['chek'])
def chek(message):
    if message.from_user.id == MY_ID:
        user = {}
        cursor.execute("SELECT * FROM schools")
        schools = cursor.fetchall()

        bot.send_message(message.from_user.id, "=== Таблица schools ===")
        for row in schools:
            user[row[1]] = f'{row[2]} \n'
        for i, j in user.items():
            bot.send_message(message.from_user.id, f'{i}: {j}')

        cursor.execute("SELECT * FROM homework")
        homework = cursor.fetchall()

        bot.send_message(message.from_user.id, "=== Таблица homework ===")
        for row in homework:
            bot.send_message(message.from_user.id, f'{row}')


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, 'Вот все команды: \n /start - пройти регистрацию (Если уже регистрировался, то тебя бот вспомнит) \n /hw - посмотреть дз\n /new_hw - добавить дз\n /tt - помсотреть рассписание \n /new_tt - изменить рассписание \n Если сменил школу, то просто введи /school')


@bot.message_handler(commands=['getdb'])
def getbd(message):
    if message.from_user.id == MY_ID:
        with open('homework.db', 'rb') as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.from_user.id, 'Не туда полез. Это команда не для тебя')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    global users
    user_id = message.from_user.id
    cursor.execute('''SELECT id, school_class FROM schools WHERE user_id = ?''', (user_id,))
    row = cursor.fetchone()
    if row:
        users[user_id] = {'school': row[1], 'reg': True}
        bot.send_message(message.from_user.id,
                         f"Привет! Напомню команды:\n /hw - посмотреть дз\n /new_hw - добавить дз\n /tt - помсотреть рассписание \n /new_tt - изменить рассписание \n Если сменил школу, то просто введи /school")
        # при следующем обновлении вырезать
        cursor.execute('''
                UPDATE homework 
                SET school_class = ? 
                WHERE school_class = ?
            ''', (rework(users[user_id]['school']), users[user_id]['school']))
        conn.commit()
        # при следующем обновлении вырезать
    else:
        bot.send_message(message.from_user.id,
                         "Привет! Это бот для хранения домашнего задания. Для начала работы бота введи название своей школы и свой класс через команду /school")


@bot.message_handler(commands=['school'])
def reg_school(message):
    user_id = message.from_user.id
    bot.send_message(message.from_user.id, "Введи название школы и класс, например: 'Лодейнопольская СОШ №3, 8а'")
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
            ''', (rework(users[user_id]['school']),))
            rows = cursor.fetchall()
            if len(rows) > 0:
                for subject, task, time, photo_id in rows:
                    hw_item.append(subject)
                    hw_chel.append(task)
                    hw_time.append(time)
                    hw_foto.append(photo_id)
                for i in range(len(hw_item)):
                    if hw_foto[i] is not None and hw_foto[i] not in ('Don`t send', 'chek in photo_id'):
                        hw_foto[i] = str(hw_foto[i]).split(', ')
                        if hw_chel[i] == 'Don`t send' or hw_chel[i] == 'chek in photo_id':
                            media_group = []
                            for j in hw_foto[i]:
                                media_group.append(types.InputMediaPhoto(j, caption=f"{hw_item[i]} (обн. {hw_time[i]})"))
                            bot.send_media_group(message.from_user.id, media=media_group)
                        elif hw_chel[i] != 'Don`t send':
                            media_group = []
                            for j in hw_foto[i]:
                                media_group.append(types.InputMediaPhoto(j, caption=f"{hw_item[i]}: {hw_chel[i]} (обн. {hw_time[i]})"))
                                bot.send_message(message.from_user.id, f'file_id = {j}\n repr = {repr(j)}')
                            bot.send_media_group(message.from_user.id, media=media_group)
                    else:
                        hw_list.append(f'- {hw_item[i]}: {hw_chel[i]} (обн. {hw_time[i]})')
                bot.send_message(message.from_user.id, f'{f'\n'.join(hw_list)}')
            else:
                bot.send_message(message.from_user.id, "Задания ещё не добавили")
        elif message.text == '/new_hw':
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            cursor.execute('SELECT * FROM homework WHERE school_class = ? ', (rework(users[user_id]['school']),))
            subject = cursor.fetchall()
            for row in subject:
                key = types.InlineKeyboardButton(text=f'{row[2]}', callback_data=f'{row[2]}')
                keyboard.add(key)
            keyboard.add(types.InlineKeyboardButton(text='Свой вариант', callback_data='Свой вариант'))
            bot.send_message(message.from_user.id,
                             text = 'Выбери один предмет из списка или добавь новый',
                             reply_markup=keyboard)
            users[user_id]['condition'] = 'wait subject'
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
                        ''', (rework(users[user_id]['school']),))
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
    global users, user_timers
    user_id = message.from_user.id
    print(f"users[{user_id}] = {users.get(user_id)}")
    print(f"condition = {users.get(user_id, {}).get('condition')}")
    if users[user_id]['condition'] == 'wait school':
        users[user_id] = {'school': message.text, 'reg': False, 'condition': 'wait school'}
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_message(message.from_user.id, text=f'Твоя школа и класс - "{users[user_id]['school']}"?',
                         reply_markup=keyboard)
    if user_id in users and users[user_id]['reg'] == True:
        if users[user_id]['condition'] == 'wait new subject':
            users[user_id]['hw_item'] = message.text
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
            keyboard.add(key_yes)
            key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_no)
            bot.send_message(message.from_user.id, text=f'Новый предмет - "{users[user_id]['hw_item']}"?',
                             reply_markup=keyboard)
        elif users[user_id]['condition'] == 'wait new hw':
            try:
                if user_id in user_timers:
                    user_timers[user_id].cancel()
                    users[user_id]['hw_foto'].append(message.photo[-1].file_id)
                else:
                    users[user_id]['hw_foto'] = ''
                    users[user_id]['hw_foto'] = [message.photo[-1].file_id]
                    users[user_id]['hw_chel'] = message.caption if message.caption else 'Don`t send'
                timer = threading.Timer(2.0, send_question, args=[user_id])
                user_timers[user_id] = timer
                timer.start()
            except:
                try:
                    users[user_id]['hw_foto'] = 'Don`t send'
                    users[user_id]['hw_chel'] = message.text
                    keyboard = types.InlineKeyboardMarkup()
                    key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
                    keyboard.add(key_yes)
                    key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
                    keyboard.add(key_no)
                    bot.send_message(message.from_user.id, f'{users[user_id]['hw_chel']}?', reply_markup=keyboard)
                except:
                    bot.send_message(message.from_user.user_id,
                                     'Ты чуть бота не сломал. Измени тип отправленного сообщения. Можно отправлять только одно/несколько фото с подписью/без подписи. Или просто текст')
        elif users[user_id]['condition'] == 'wait new tt':
            users[user_id]['tt'] = message.photo[-1].file_id
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
            keyboard.add(key_yes)
            key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_no)
            bot.send_photo(message.from_user.id, caption=f'Рассписание на завтра?', photo=users[user_id]['tt'], reply_markup=keyboard)
        else:
            bot.send_message(message.from_user.id, 'Я тебя не понимаю. Введи /help, для просмотра команд. Или можешь подать жалобу через /feedback, а я через время отвечу')
    else:
        bot.send_message(message.from_user.user_id, 'Сначала пройди регистрацию через /start')


@bot.message_handler(content_types=['document'])
def handle_document(message):
    if message.from_user.id == MY_ID:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('homework.db', 'wb') as f:
            f.write(downloaded_file)
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, subject TEXT, task TEXT, time INTEGER, photo_id TEXT, UNIQUE(school_class, subject))''')
        bot.reply_to(message, "База данных обновлена")
    else:
        bot.reply_to(message, "Недоступно")



@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global users
    user_id = call.from_user.id
    if users[user_id]['condition'] == 'wait school':
        if call.data == "yes":
            bot.send_message(call.message.chat.id,
                             'Хорошо. Теперь ты можешь посмотреть дз (/hw) или ввести новое(/new_hw). Ещё ты можешь посмотреть рассписание (/tt) ли обновить (/new_tt)')
            cursor.execute('''
                       INSERT INTO schools (user_id, school_class)
                       VALUES (?, ?)
                       ''', (user_id, rework(users[user_id]['school'])))
            conn.commit()
            users[user_id]['condition'] = ''
            users[user_id]['reg'] = True
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /school')
    elif users[user_id]['condition'] =='wait subject':
        if call.data == "Свой вариант":
            bot.send_message(call.message.chat.id, 'Тогда жду предмет')
            users[user_id]['condition'] = 'wait new subject'
        elif call.data:
            bot.send_message(call.message.chat.id, 'Тогда можешь отправить одно или несколько фото дз с подисью или без. Или без фото')
            users[user_id]['hw_item'] = call.data
            users[user_id]['condition'] = 'wait new hw'
    elif users[user_id]['condition'] == 'wait new subject':
        if call.data == 'yes':
            bot.send_message(call.message.chat.id, 'Тепрь можешь отправить одно или несколько фото дз с подписью или без. Можешь отправить и один текст без фотки')
            users[user_id]['condition'] = 'wait new hw'
        elif call.data == 'no':
            bot.send_message(call.message.chat.id, 'Тогда введи заново')
    elif users[user_id]['condition'] == 'wait new hw':
        if call.data == "yes":
            now_utc = datetime.now(timezone.utc)
            now_msk = now_utc + timedelta(hours=3)
            if users[user_id]['hw_foto'] != 'Don`t send':
                cursor.execute('''
                INSERT OR REPLACE INTO homework (school_class, subject, task, time, photo_id)
                VALUES (?, ?, ?, ?, ?)
                ''', (rework(users[user_id]['school']), users[user_id]['hw_item'], users[user_id]['hw_chel'],
                      now_msk.strftime('%d.%m в %H:%M'), ', '.join(users[user_id]['hw_foto'])))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO homework (school_class, subject, task, time, photo_id)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (rework(users[user_id]['school']), users[user_id]['hw_item'], users[user_id]['hw_chel'],
                      now_msk.strftime('%d.%m в %H:%M'), users[user_id]['hw_foto']))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Можешь добавить ещё дз через /new_hw, или посмотреть дз через /hw')
            users[user_id]['hw_foto'] = ''
            users[user_id]['hw_chel'] = ''
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_hw')
    elif users[user_id]['condition'] == 'wait new tt':
        if call.data == "yes":
            now_utc = datetime.now(timezone.utc)
            now_msk = now_utc + timedelta(hours=3)
            cursor.execute('''
            INSERT OR REPLACE INTO timetable (school_class, timetable, time)
            VALUES (?, ?, ?)
            ''', (rework(users[user_id]['school']), users[user_id]['tt'], now_msk.strftime('%d.%m в %H:%M')))
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