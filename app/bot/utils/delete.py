from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
import asyncio

async def delete_previous_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, limit=50):
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    context.user_data['current_order_id'] = None
    tasks = []
    for i in range(message_id - 1, max(message_id - limit, 0), -1):
        tasks.append(context.bot.delete_message(chat_id=chat_id, message_id=i))
    await asyncio.gather(*tasks, return_exceptions=True)