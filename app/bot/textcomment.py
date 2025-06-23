from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
from app import create_app, db
from datetime import datetime
from app.models import Comment, Order
from app.bot.notf import send_notification

app = create_app()

async def handle_text_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('create_mode'):
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        telegram_id = update.message.from_user.id
        user = next((user for user in Config.users if user['telegram_id'] == str(telegram_id)), None)
        if not user:
            return
        order_id = context.user_data.get('current_order_id')
        if not order_id:
            await update.message.reply_text("Заказ не найден для добавления комментария.")
            return
        with app.app_context():
            comment = Comment(
                datetime = datetime.now(),
                text=update.message.text,
                user_id=user['user_id'],
                order_id=order_id
            )
            db.session.add(comment)
            db.session.commit()
            order = Order.query.filter(Order.id == order_id).first()
            notf = f"<blockquote>💬 <b>Новый комментарий</b>\n{order.address}</blockquote>\n\n<b>👷 {comment.user.name}\n----------------------------------------</b>\n{comment.text}"
            await send_notification(order.manufacturer_id if str(order.manufacturer_id) != user['user_id'] else '',
                                    notf,
                                    order_id,
                                    False)
            await send_notification('',
                                    notf,
                                    order_id,
                                    True)
            from app.routes.utils.new import new
            new(order_id, user['user_id'])
        await update.message.reply_text("Комментарий отправлен!")