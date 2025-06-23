from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
import asyncio, uuid, os
from datetime import datetime
from app import db, create_app
from app.routes.utils.createthumbnail import create_thumbnail
from app.models import Comment, CommentPhoto, Order
from app.bot.notf import send_notification

app = create_app()

MEDIA_GROUP_DELAY = 1

async def handle_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('create_mode'):
        telegram_id = update.message.from_user.id
        user = next((user for user in Config.users if user['telegram_id'] == str(telegram_id)), None)
        if not user:
            return
        order_id = context.user_data.get('current_order_id')
        if not order_id:
            await update.message.reply_text("Заказ не найден для добавления комментария.")
            return
        media_group = update.message.media_group_id
        if media_group is None:
            return await handle_single_photo(update, context, user, order_id)
        group_messages = context.bot_data.setdefault(media_group, [])
        group_messages.append(update.message)
        if 'media_group_timer' not in context.chat_data:
            context.chat_data['media_group_timer'] = asyncio.create_task(
                delayed_process_media_group(update, context, media_group, user, order_id)
            )

async def delayed_process_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE, media_group_id: str, user, order_id):
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(MEDIA_GROUP_DELAY)
    group_messages = context.bot_data.pop(media_group_id, [])
    if group_messages:
        await process_media_group(update, context, group_messages, user, order_id)
    if 'media_group_timer' in context.chat_data:
        del context.chat_data['media_group_timer']

async def handle_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, user, order_id):
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    with app.app_context():
        text = update.message.caption if update.message.caption else ""
        comment = Comment(
            datetime=datetime.now(),
            text=text,
            user_id=user['user_id'],
            order_id=order_id
        )
        db.session.add(comment)
        db.session.commit()
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        file_extension = os.path.splitext(file.file_path)[1]
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join('app', 'static', 'photo', file_name)
        await file.download_to_drive(file_path)
        thumbnail_name = f"thumb_{file_name}"
        thumbnail_path = os.path.join('app', 'static', 'photo', thumbnail_name)
        create_thumbnail(file_path, thumbnail_path)
        comment_photo = CommentPhoto(
            comment_id=comment.id,
            path=file_name,
            small_path=thumbnail_name
        )
        db.session.add(comment_photo)
        db.session.commit()
        from app.routes.utils.new import new
        new(order_id, user['user_id'])
        order = Order.query.filter(Order.id == order_id).first()
        text = 'Без текста' if text == '' else text
        attach = f'<b>\n\nПрикреплено: 1 фото</b>'
        notf = f"<blockquote>💬 <b>Новый комментарий</b>\n{order.address}</blockquote>\n\n<b>👷 {user['name']}\n----------------------------------------</b>\n{text}{attach}"
        await send_notification(order.manufacturer_id if str(order.manufacturer_id) != user['user_id'] else '',
                                notf,
                                order_id,
                                False)
        await send_notification('',
                                notf,
                                order_id,
                                True)
        
    await update.message.reply_text("Комментарий с фото отправлен!")

async def process_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE, messages, user, order_id):
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    with app.app_context():
        text = next((msg.caption for msg in messages if msg.caption), "") or ""
        comment = Comment(
            datetime=datetime.now(),
            text=text,
            user_id=user['user_id'],
            order_id=order_id
        )
        db.session.add(comment)
        db.session.commit()
        for message in messages:
            if message.photo:
                photo = message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                file_extension = os.path.splitext(file.file_path)[1]
                file_name = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join('app', 'static', 'photo', file_name)
                await file.download_to_drive(file_path)
                thumbnail_name = f"thumb_{file_name}"
                thumbnail_path = os.path.join('app', 'static', 'photo', thumbnail_name)
                create_thumbnail(file_path, thumbnail_path)
                comment_photo = CommentPhoto(
                    comment_id=comment.id,
                    path=file_name,
                    small_path=thumbnail_name
                )
                db.session.add(comment_photo)
        db.session.commit()
        from app.routes.utils.new import new
        new(order_id, user['user_id'])
        order = Order.query.filter(Order.id == order_id).first()
        attach = f'<b>\n\nПрикреплено: {len(messages)} фото</b>'
        text = 'Без текста' if text == '' else text
        notf = f"<blockquote>💬 <b>Новый комментарий</b>\n{order.address}</blockquote>\n\n<b>👷 {user['name']}\n----------------------------------------</b>\n{text}{attach}"
    await context.bot.send_message(chat_id=messages[0].chat_id, text="Комментарий с фото отправлен!")
    await send_notification(order.manufacturer_id if str(order.manufacturer_id) != user['user_id'] else '',
                            notf,
                            order_id,
                            False)
    await send_notification('',
                            notf,
                            order_id,
                            True)