
import telebot
import logging
import sqlite3

# Токен вашего бота
BOT_TOKEN = "7532072705:AAG-ARMxVkTD1ebDkIEiLDfPrCroX2Un1J8 "

# ID админов
ADMIN_ID = 6399609937 # Замените на ваш ID!
CO_ADMIN_ID = 1286103232 # Замените на ID совладельца!

# Список админов
admins = [ADMIN_ID, CO_ADMIN_ID]

# Настройка логгирования
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(BOT_TOKEN)

# Состояния
START = "start"
CHAIN = "chain"
REQUEST = "request"

# Словарь для хранения состояния пользователя
user_states = {} 

# Функция для пересылки сообщения всем админам
def forward_to_admins(message):
    for admin_id in admins:
        bot.forward_message(chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id)

# Функция для создания таблицы в базе данных
def create_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            request_type TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

create_db()

# Функция для сохранения запроса в базу данных
def save_request(user_id, request_type, message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO requests (user_id, request_type, message) VALUES (?, ?, ?)", (user_id, request_type, message))
    conn.commit()
    conn.close()

# Обработчики сообщений

@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == 'private')
def handle_start(message):
    logging.info(f"Пользователь @{message.from_user.username} начал диалог.")
    user_states[message.chat.id] = START
    bot.send_message(message.chat.id, "Старт. Продолжить?", reply_markup=generate_start_markup())

@bot.message_handler(func=lambda message: user_states[message.chat.id] == START and message.chat.type == 'private')
def handle_start_continue(message):
    if message.text == "Продолжить":
        user_states[message.chat.id] = CHAIN
        bot.send_message(message.chat.id, "Цепочка сообщений:", reply_markup=generate_chain_markup())
    else:
        bot.send_message(message.chat.id, "Неверный вариант. Попробуйте снова.")

@bot.message_handler(func=lambda message: user_states[message.chat.id] == CHAIN and message.chat.type == 'private')
def handle_chain(message):
    if message.text == "Предложить видео":
        user_states[message.chat.id] = REQUEST
        bot.send_message(message.chat.id, "Заявка:", reply_markup=generate_request_markup())
        forward_to_admins(message)
        logging.info(f"Переслано видео от @{message.from_user.username} админам.")
        save_request(message.chat.id, "видео", message.text)
    elif message.text == "Предложить цитату":
        user_states[message.chat.id] = REQUEST
        bot.send_message(message.chat.id, "Заявка:", reply_markup=generate_request_markup())
        forward_to_admins(message)
        logging.info(f"Переслана цитата от @{message.from_user.username} админам.")
        save_request(message.chat.id, "цитата", message.text)
    elif message.text == "Донат":
        user_states[message.chat.id] = REQUEST
        bot.send_message(message.chat.id, "Заявка:", reply_markup=generate_request_markup())
    elif message.text == "Любая другая фраза":
        bot.send_message(message.chat.id, "Хорошо!")
        user_states[message.chat.id] = CHAIN
        bot.send_message(message.chat.id, "Цепочка сообщений:", reply_markup=generate_chain_markup())
    elif message.text == "Назад":
        user_states[message.chat.id] = START
        bot.send_message(message.chat.id, "Старт. Продолжить?", reply_markup=generate_start_markup())
    else:
        bot.send_message(message.chat.id, "Неверный вариант. Попробуйте снова.")

@bot.message_handler(func=lambda message: user_states[message.chat.id] == REQUEST and message.chat.type == 'private')
def handle_request(message):
    # Обработка запроса (например, сохранение данных о заявке)
    bot.send_message(message.chat.id, "Заявка обработана.")
    user_states[message.chat.id] = CHAIN
    bot.send_message(message.chat.id, "Цепочка сообщений:", reply_markup=generate_chain_markup())

# Функции для создания клавиатур (reply_markup)
def generate_start_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Продолжить")
    return markup

def generate_chain_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Предложить видео", "Предложить цитату", "Донат", "Любая другая фраза", "Назад")
    return markup

def generate_request_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Продолжить")
    return markup

bot.polling()
