from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from app.models import Order
from sqlalchemy import asc, nulls_last
from app import create_app
# from .utils.delete import delete_previous_messages
from datetime import datetime
from config import Config
import asyncio

app = create_app()

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('create_mode'):
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        try:
            previous_messages_ids = context.user_data.get('last_message_ids', [])
            if previous_messages_ids:
                await delete_messages(update.effective_chat.id, context.bot, previous_messages_ids)
        except:
            pass
        # await delete_previous_messages(update, context)
        orders_list = []
        with app.app_context():
            telegram_id = update.message.from_user.id
            user = next((user for user in Config.users if user['telegram_id'] == str(telegram_id)), None)
            if not user:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Перешлите этот номер разработчику для добавления в систему: " + str(update.message.from_user.id))
                return False
            if user['role'] == '1':
                orders = Order.query.filter(Order.status_id.notin_([3, 5, 6, 7])).order_by(nulls_last(asc(Order.deadline))).all()
            else:
                orders = Order.query.filter(Order.manufacturer_id == user['user_id']).filter(Order.status_id.notin_([3, 5, 6, 7])).order_by(nulls_last(asc(Order.deadline))).all()
            for order in orders:
                deadline = ''
                statuses = {1: '🟢', 2: '🟡', 4: '🔴'}
                status = statuses[order.status_id]
                address = order.address
                if order.deadline:
                    deadline_dt = datetime.strptime(str(order.deadline), "%Y-%m-%d %H:%M:%S")
                    deadline = deadline_dt.strftime("%a, %d.%m %H:%M")
                else:
                    deadline = 'Нет'
                orders_list.append({'text': f'{deadline} | {status} | {address}', 'command': f"/order {order.id}"})
        keyboard = [[InlineKeyboardButton(order["text"], callback_data=order["command"])] for order in orders_list]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if len(orders_list) > 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Ваши заказы:", reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Заказов пока нет")
            
async def delete_messages(chat_id, bot, message_ids):
    tasks = []
    for message_id in message_ids:
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=message_id))
    await asyncio.gather(*tasks)