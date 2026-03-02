import telebot
from telebot import types
import sqlite3
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

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS schools (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, school_class TEXT)''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS homework (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, subject TEXT, task TEXT, time INTEGER, photo_id TEXT, UNIQUE(school_class, subject))''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS timetable (id INTEGER PRIMARY KEY AUTOINCREMENT, school_class INTEGER, timetable TEXT, time INTEGER, UNIQUE(school_class, timetable))''')

cursor.execute(
    '''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, problem TEXT, photo_id TEXT, verified INTEGER DEFAULT 0)''')

conn.commit()

@bot.message_handler(commands=['chek'])
def chek(message):
    if message.from_user.id == MY_ID:
        jlst = []

        cursor.execute("SELECT * FROM schools")
        schools = cursor.fetchall()

        cursor.execute("SELECT * FROM homework")
        homework = cursor.fetchall()

        bot.send_message(message.from_user.id, "=== Таблица schools ===")
        for row in schools:
            jlst.append(row)
        bot.send_message(message.from_user.id, f'{f'\n'.join(jlst)}')

        bot.send_message(message.from_user.id, "=== Таблица homework ===")
        for row in homework:
            jlst.append(row)
            bot.send_message(message.from_user.id, f'{f'\n '.join(jlst)}')


@bot.message_handler(commands=['feedback'])
def feedback(message):
    global users
    user_id = message.from_user.id
    bot.send_message(message.from_user.id, 'Хорошо, отправь фото проблемы и описание. Ответ ожидай в ближайщее время')
    users[user_id]['condition'] = 'wait problem'


@bot.message_handler(commands=['get_feedback'])
def get_feedback(message):
    if message.from_user.id == MY_ID:
        jlst = []

        cursor.execute("SELECT * FROM feedback")
        feedback = cursor.fetchall()

        bot.send_message(message.from_user.id, "=== Таблица feedback ===")
        for row in feedback:
            if row[3] == 0:
                jlst.append(row)
        bot.send_message(message.from_user.id, f'{f'\n'.join(jlst)}')


@bot.message_handler(commands=['replay'])
def replay(message):
    global users
    user_id = message.from_user.id
    if user_id == MY_ID:
        bot.send_message(message.from_user.id, 'Жду')
        users[user_id]['condition'] = 'wait replay'


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, 'Вот все команды: \n /start - пройти регистрацию (Если уже регистрировался, то тебя бот вспомнит) \n /hw - посмотреть дз\n /new_hw - добавить дз\n /tt - помсотреть рассписание \n /new_tt - изменить рассписание \n Если сменил школу, то просто введи /school \n Если хочешь отпраить жалобу или задать вопрос, то напиши /feedback')


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
                         f"Привет! Напомню команды:\n /hw - посмотреть дз\n /new_hw - добавить дз\n /tt - помсотреть рассписание \n /new_tt - изменить рассписание \n Если сменил школу, то просто введи /school \n Если хочешь отпраить жалобу или задать вопрос, то напиши /feedback")
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
                        bot.send_photo(message.from_user.id, photo=hw_foto[i], caption=f" {hw_item[i]} (обн. {hw_time[i]})")
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
    elif users[user_id]['condition'] == 'wait problem':
        try:
            users[user_id]['problem_foto'] = message.photo[-1].file_id
            users[user_id]['problem_text'] = message.text
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
            keyboard.add(key_yes)
            key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_no)
            bot.send_photo(message.from_user.id, caption=f'Твоя проблема: {users[user_id]['problem_text']}', photo=users[user_id]['problem_foto'], reply_markup=keyboard)
        except:
            users[user_id]['problem_foto'] = 'Don`t send'
            users[user_id]['problem_text'] = message.text
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
            keyboard.add(key_yes)
            key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_no)
            bot.send_message(message.from_user.id, f'Уверен?: {users[user_id]['problem_text']}', reply_markup=keyboard)
    elif users[user_id]['condition'] == 'wait replay':
        if message.from_user.id == MY_ID:
            users[user_id]['id'] = message.text.split(': ')[0]
            users[user_id]['answer'] = message.text.split(': ')[1]
            keyboard = types.InlineKeyboardMarkup()
            key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
            keyboard.add(key_yes)
            key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
            keyboard.add(key_no)
            bot.send_message(message.from_user.id, f'айди пользователя: {users[user_id]['id']}, ответ: {users[user_id]['answer']}', reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, 'Я тебя не понимаю. Введи /help, для просмотра команд. Или можешь подать жалобу через /feedback, а я через время отвечу')


@bot.message_handler(content_types=['document'])
def handle_document(message):
    if message.from_user.id == MY_ID:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('homework.db', 'wb') as f:
            f.write(downloaded_file)
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
                       ''', (user_id, users[user_id]['school']))
            conn.commit()
            users[user_id]['condition'] = ''
            users[user_id]['reg'] = True
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /school')
    elif users[user_id]['condition'] == 'wait new hw':
        if call.data == "yes":
            now_utc = datetime.now(timezone.utc)
            now_msk = now_utc + timedelta(hours=3)
            cursor.execute('''
            INSERT OR REPLACE INTO homework (school_class, subject, task, time)
            VALUES (?, ?, ?, ?)
            ''', (users[user_id]['school'], users[user_id]['item'], users[user_id]['chel'], now_msk.strftime('%d.%m в %H:%M')))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Если хочешь ввести ещё дз, то используй команду /new_hw ещё раз')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_hw')
    elif users[user_id]['condition'] == 'wait photo':
        if call.data == "yes":
            now_utc = datetime.now(timezone.utc)
            now_msk = now_utc + timedelta(hours=3)
            cursor.execute('''
            INSERT OR REPLACE INTO homework (school_class, subject, task, time, photo_id)
            VALUES (?, ?, ?, ?, ?)
            ''', (users[user_id]['school'], users[user_id]['item'], 'chek in photo_id', now_msk.strftime('%d.%m в %H:%M'), users[user_id]['chel']))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Если хочешь ввести ещё дз, то используй команду /new_hw ещё раз')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_hw')
    elif users[user_id]['condition'] == 'wait new tt':
        if call.data == "yes":
            now_utc = datetime.now(timezone.utc)
            now_msk = now_utc + timedelta(hours=3)
            cursor.execute('''
            INSERT OR REPLACE INTO timetable (school_class, timetable, time)
            VALUES (?, ?, ?)
            ''', (users[user_id]['school'], users[user_id]['tt'], now_msk.strftime('%d.%m в %H:%M')))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Если хочешь обновить рассписание, то используй команду /new_tt ещё раз')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /new_tt')
    elif users[user_id]['condition'] == 'wait problem':
        if call.data == "yes":
            cursor.execute('''
            INSERT OR REPLACE INTO feedback (problem, photo_id)
            VALUES (?, ?)
            ''', (users[user_id]['problem_text'], users[user_id]['problem_foto']))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.chat.id,
                             'Хорошо. Жди ответа в ближайшее время')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /feedback')
    elif users[user_id]['condition'] == 'wait replay':
        if call.data == "yes":
            cursor.execute('''
            INSERT OR REPLACE INTO feedback (verified)
            VALUES (?)
            ''', (1,))
            conn.commit()
            users[user_id]['condition'] = ''
            bot.send_message(call.message.users[user_id]['id'], f'Вот ответ от разработчика: {users[user_id]["answer"]}')
            bot.send_message(call.message.chat.id, 'Отправил')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Тогда введи заново через /feedback')


keep_alive()
while True:
    try:
        bot.polling(none_stop=True, interval=0)
        # если возникла ошибка — сообщаем про исключение и продолжаем работу
    except Exception as e:
        now = datetime.now().strftime('%d.%m в %H:%M:%S')
        print(f'❌❌❌❌❌ Сработало исключение! ❌❌❌❌❌ {now}')
