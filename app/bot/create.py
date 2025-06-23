from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
from g4f.client import Client
import re, json
from datetime import datetime

client = Client()

order = {'Customer': '',
         'Phone': '',
         'Address': '',
         'Price': '',
         'Prepayment': '',
         'Deadline': '',
         'Desc': '',
         'Edit': False}

async def create (update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    telegram_id = update.message.from_user.id
    user = next((user for user in Config.users if user['telegram_id'] == str(telegram_id)), None)
    if not user or user['role'] != '1':
        return await context.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка доступа")
    context.user_data['create_mode'] = True
    keyboard = [
        [InlineKeyboardButton("Отмена", callback_data="/cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await context.bot.send_message(chat_id=update.effective_chat.id,
                                          text="Расскажите мне о заказе, чтобы я его мог добавить\n\n<blockquote>Заказчик\nНомер телефона\nАдрес\nЦена\nПредоплата\nДата изготовления\nОписание</blockquote>",
                                          reply_markup=reply_markup,
                                          parse_mode='html')

async def cancel (update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)
    await query.answer()
    command = query.data
    if command == '/cancel':
        if context.user_data.get('create_mode'):
            context.user_data['create_mode'] = False
            order['Customer'] = ''
            order['Phone'] = ''
            order['Address'] = ''
            order['Price'] = ''
            order['Prepayment'] = ''
            order['Deadline'] = ''
            order['Desc'] = ''
            order['Edit'] = False
            return await context.bot.send_message(chat_id=update.effective_chat.id, text="Отмена")
        
async def create_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('create_mode'):
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        if not order['Edit']:
            text = f'Текст "{update.message.text}"'
            prompt = 'Анализируй следующий текст и извлеки из него данные о заказе. Пожалуйста, предоставь результат в формате JSON, содержащий следующие поля: Customer, Phone, Address, Price, Prepayment, Deadline, Desc. Поля без данных пометь как "None", Телефон всегда Российский, запиши его в международном формате, Deadline в формате datetime'
            response = query(f'{prompt} {text}')
            json_from_response = extract_json(response)
            order['Customer'] = json_from_response['Customer'] if json_from_response['Customer'] != "None" else ''
            order['Phone'] = json_from_response['Phone'] if json_from_response['Phone'] != "None" else ''
            order['Address'] = json_from_response['Address'] if json_from_response['Address'] != "None" else ''
            order['Price'] = json_from_response['Price'] if json_from_response['Price'] != "None" else ''
            order['Prepayment'] = json_from_response['Prepayment'] if json_from_response['Prepayment'] != "None" else ''
            order['Deadline'] = deadline_convert(json_from_response['Deadline'])
            order['Desc'] = json_from_response['Desc'] if json_from_response['Desc'] != "None" else ''
            order['Edit'] = True
        else:
            response = query(f'НИ В КОЕМ СЛУЧАЕ НЕ УДАЛЯЙ ПОЛЯ ИЗ JSON!!! Привет, я хочу изменить свой JSON, в ответ хочу получить только JSON. Телефон Российский в международном формате. Дата в формате Datetime. {update.message.text}. Вот сам JSON {json.dumps(order)}')
            json_from_response = extract_json(response)
            order['Customer'] = json_from_response['Customer'] if json_from_response['Customer'] != "None" else ''
            order['Phone'] = json_from_response['Phone'] if json_from_response['Phone'] != "None" else ''
            order['Address'] = json_from_response['Address'] if json_from_response['Address'] != "None" else ''
            order['Price'] = json_from_response['Price'] if json_from_response['Price'] != "None" else ''
            order['Prepayment'] = json_from_response['Prepayment'] if json_from_response['Prepayment'] != "None" else ''
            order['Deadline'] = deadline_convert(json_from_response['Deadline'])
            order['Desc'] = json_from_response['Desc'] if json_from_response['Desc'] != "None" else ''
        keyboard = [
            [InlineKeyboardButton("Отмена", callback_data="/cancel")]
        ]
        if can_create():
            keyboard.append([InlineKeyboardButton("Создать", callback_data="/add")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        user_response = f'Заказчик: {order['Customer']}\nТелефон: {order['Phone']}\nАдрес: {order['Address']}\nЦена: {order['Price']}\nПредоплата: {order['Prepayment']}\nДата изготовления: {order['Deadline']}\nОписание: {order['Desc']}'
        return await context.bot.send_message(chat_id=update.effective_chat.id, text=user_response, reply_markup=reply_markup)
    
def can_create():
    if order['Customer'] != '' and re.match(r'^\+7\d{10}$', order['Phone']) and order['Address'] != '':
        return True
    
def extract_json(text):
    try:
        json_str = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_str:
            return json.loads(json_str.group())
        else:
            return None
    except json.JSONDecodeError:
        return None

def query(q):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": q}]
    )
    return response.choices[0].message.content

def deadline_convert(datetime_str):
    formats = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']
    for fmt in formats:
        try:
            return str(datetime.strptime(datetime_str, fmt))
        except ValueError:
            continue
    return ''

# СОХРАНЕНИЕ ЗАКАЗА, ГОЛОСОВОЙ ВВОД, ФОРМАТИРОВАНИЕ ДАТЫ ДЛЯ ОТОБРАЖЕНИЯ