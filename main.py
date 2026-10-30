import telebot
from telebot import types
import os
import time

# --- НАСТРОЙКИ (берутся из настроек хостинга) ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN)

ITEMS = [
    "Молоко", "Хлеб", "Яйца", "Сахар", "Соль",
    "Чай", "Кофе", "Сливочное масло", "Мука", "Рис",
    "Макароны", "Кетчуп", "Майонез", "Салфетки", "Мыло",
    "Шампунь", "Зубная паста", "Туалетная бумага", "Губки", "Мусорные пакеты"
]

selections = {}

def build_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    user_selections = selections.get(user_id, [])
    
    for item in ITEMS:
        if item in user_selections:
            text = f"✅ {item}"
        else:
            text = f"➕ {item}"
        markup.add(types.InlineKeyboardButton(text, callback_data=f"item_{item}"))
    
    markup.add(types.InlineKeyboardButton("📤 Сформировать и отправить список", callback_data="send_list"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    selections[user_id] = []
    markup = build_keyboard(user_id)
    bot.send_message(message.chat.id, "📋 Выберите позиции, которые нужно дозаказать:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        user_id = call.from_user.id
        if user_id not in selections:
            selections[user_id] = []
        
        if call.data == "send_list":
            selected = selections.get(user_id, [])
            if not selected:
                bot.answer_callback_query(call.id, "⚠️ Вы ничего не выбрали!", show_alert=True)
                return
            
            text = "🚨 *Новый заказ на дозаказ:*\n\n" + "\n".join([f"▪️ {item}" for item in selected])
            
            try:
                bot.send_message(TARGET_CHAT_ID, text, parse_mode="Markdown")
                bot.answer_callback_query(call.id, "✅ Список успешно отправлен!")
                bot.send_message(call.message.chat.id, "✅ Отлично! Список отправлен ответственному.")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Ошибка отправки: проверьте, нажал ли получатель /start в боте", show_alert=True)
            
            selections[user_id] = []
        else:
            item_name = call.data.replace("item_", "")
            if item_name in selections[user_id]:
                selections[user_id].remove(item_name)
                bot.answer_callback_query(call.id, f"❌ {item_name} убран")
            else:
                selections[user_id].append(item_name)
                bot.answer_callback_query(call.id, f"✅ {item_name} добавлен")
            
            new_markup = build_keyboard(user_id)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=new_markup)
    
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")

print("Бот запущен и работает!")

# Стабильный цикл с автопереподключением
while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Ошибка подключения: {e}. Переподключение...")
        time.sleep(5)