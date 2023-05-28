import telebot
import threading
import json
import datetime

# Константи
TOKEN = 'TOKEN HERE'
TASKS_FILE = 'tasks.json'
TIMERS_FILE = 'timers.json'

# Ініціалізуємо бота
bot = telebot.TeleBot(TOKEN)

# Ініціалізуємо дані
tasks = []
timers = {}

#=========================================================================================================Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Ласкаво просимо до бота-тайм-менеджера! \nВикористайте /help для перегляду списку доступних команд.')


#==========================================================================================================Команда /help
@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, '/new_task     - Створити нове завдання.\n'
                              '/list_tasks   - Список всіх завдань.\n'
                              '/edit_task    - Редагувати існуюче завдання.\n'
                              '/set_timer    - Встановити таймер для завдання.\n'
                              '/cancel_timer - Скасувати таймер.\n'
                              '/delete_task  - Видалити існуюче завдання.\n')

#======================================================================================================Команда /new_task
@bot.message_handler(commands=['new_task'])
def new_task(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введіть назву завдання:')
    bot.register_next_step_handler(message, new_task_name)

def new_task_name(message):
    chat_id = message.chat.id
    task_name = message.text
    bot.send_message(chat_id, 'Введіть опис завдання:')
    bot.register_next_step_handler(message, new_task_description, task_name)

def new_task_description(message, task_name):
    chat_id = message.chat.id
    task_description = message.text

    if len(tasks) > 0:
        last_task = tasks[-1]
        last_task_id = last_task['task_id']
        new_task_id = last_task_id + 1
    else:
        new_task_id = 1

    user_id = message.from_user.id
    task = {
        'user_id': user_id,
        'task_id': new_task_id,
        'task_name': task_name,
        'task_description': task_description,
        'status': 'Виконується'
    }
    tasks.append(task)
    save_tasks()
    bot.send_message(chat_id, 'Завдання успішно створено!')
    bot.send_message(chat_id, get_task_message(task))

#====================================================================================================Команда /list_tasks
@bot.message_handler(commands=['list_tasks'])
def list_tasks(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_tasks = [task for task in tasks if task['user_id'] == user_id]
    if len(user_tasks) == 0:
        bot.send_message(chat_id, 'Завдань не знайдено.')
    else:
        for task in user_tasks:
            bot.send_message(chat_id, get_task_message(task))

#=====================================================================================================Команда /edit_task
@bot.message_handler(commands=['edit_task'])
def edit_task(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введіть ID завдання:')
    bot.register_next_step_handler(message, edit_task_id)

def edit_task_id(message):
    chat_id = message.chat.id
    task_id = message.text
    if not task_id.isdigit():
        bot.send_message(chat_id, 'Ви вказали невірний формат.')
        return
    task_id = int(task_id)
    task_index = get_task_index(task_id)
    if task_index is None:
        bot.send_message(chat_id, 'Завдання не знайдено.')
    else:
        task = tasks[task_index]
        bot.send_message(chat_id, 'Введіть нову назву завдання:')
        bot.register_next_step_handler(message, edit_task_name, task)

def edit_task_name(message, task):
    chat_id = message.chat.id
    task_name = message.text
    task['task_name'] = task_name
    save_tasks()
    bot.send_message(chat_id, 'Введіть новий опис завдання:')
    bot.register_next_step_handler(message, edit_task_description, task)

def edit_task_description(message, task):
    chat_id = message.chat.id
    task_description = message.text
    task['task_description'] = task_description
    save_tasks()
    bot.send_message(chat_id, get_task_message(task))


#===================================================================================================Команда /delete_task
@bot.message_handler(commands=['delete_task'])
def delete_task(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введіть ID завдання:')
    bot.register_next_step_handler(message, delete_task_id)

def delete_task_id(message):
    chat_id = message.chat.id
    task_id = message.text
    if not task_id.isdigit():
        bot.send_message(chat_id, 'Ви вказали невірний формат.')
        return
    chat_id = message.chat.id
    task_id = int(message.text)
    task_index = get_task_index(task_id)
    if task_index is None:
        bot.send_message(chat_id, 'Завдання не знайдено.')
    else:
        tasks.pop(task_index)
        save_tasks()
        bot.send_message(chat_id, 'Завдання успішно видалено!')

#=====================================================================================================Команда /set_timer
@bot.message_handler(commands=['set_timer'])
def set_timer(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введіть ID завдання:')
    bot.register_next_step_handler(message, set_timer_id)

def set_timer_id(message):
    chat_id = message.chat.id
    task_id = message.text
    if not task_id.isdigit():
        bot.send_message(chat_id, 'Ви вказали невірний формат.')
        return
    task_id = int(task_id)
    task_index = get_task_index(task_id)
    if task_index is None:
        bot.send_message(chat_id, 'Завдання не знайдено.')
    else:
        task = tasks[task_index]
        if task_id in timers:
            bot.send_message(chat_id, 'На це завдання вже встановлений таймер.')
        else:
            bot.send_message(chat_id, 'Введіть час у хвилинах:')
            bot.register_next_step_handler(message, set_timer_time, task)

def set_timer_time(message, task):
    chat_id = message.chat.id
    time = int(message.text)
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=time)
    timers[task['task_id']] = {'end_time': end_time.timestamp(), 'chat_id': chat_id, 'message_id': None}
    save_timers()
    bot.send_message(chat_id, 'Таймер встановлено успішно!')

    timer_id = task['task_id']
    timer_interval = time * 60
    timer = threading.Timer(timer_interval, timer_callback, args=[chat_id, timer_id])
    timer.start()

def timer_callback(chat_id, timer_id):
    task_index = get_task_index(timer_id)
    if task_index is not None:
        task = tasks[task_index]
        bot.send_message(chat_id, f'Таймер для завдання "{task["task_name"]}" закінчився!')
        del timers[timer_id]
        save_timers()
#==================================================================================================Команда /cancel_timer
@bot.message_handler(commands=['cancel_timer'])
def cancel_timer(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введіть ID завдання:')
    bot.register_next_step_handler(message, cancel_timer_id)

def cancel_timer_id(message):
    chat_id = message.chat.id
    task_id = message.text
    if not task_id.isdigit():
        bot.send_message(chat_id, 'Ви вказали невірний формат.')
        return
    chat_id = message.chat.id
    task_id = int(message.text)
    if task_id not in timers:
        bot.send_message(chat_id, 'Таймер не знайдено.')
    else:
        timer = timers[task_id]
        if timer['message_id'] is not None:
            bot.delete_message(chat_id, timer['message_id'])
        del timers[task_id]
        save_timers()
        bot.send_message(chat_id, 'Таймер успішно скасовано!')

def get_task_index(task_id):
    for i in range(len(tasks)):
        if tasks[i]['task_id'] == task_id:
            return i
    return None

def get_task_message(task):
    task_message = f"ID: {task['task_id']}\nТема: {task['task_name']}\nОпис: {task['task_description']}\nСтатус: {task['status']}"
    return task_message

def save_tasks():
    with open(TASKS_FILE, 'w') as f:
        tasks_to_save = [dict(task, user_id=str(task['user_id'])) for task in tasks]
        json.dump(tasks_to_save, f, indent=4)

def load_tasks():
    with open('tasks.json', 'r') as f:
        tasks = json.load(f)
    for task in tasks:
        if 'user_id' in task:
            task['user_id'] = int(task['user_id'])
    return tasks

def save_timers():
    with open(TIMERS_FILE, 'w') as f:
        json.dump(timers, f)

def load_timers():
    global timers
    try:
        with open(TIMERS_FILE, 'r') as f:
            timers = json.load(f)
    except FileNotFoundError:
        timers = {}

load_tasks()
load_timers()

bot.polling(none_stop=True)
