from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from config import Config
import urllib.parse
from app.models import Order, Comment
from babel.dates import format_date
from app import create_app
from flask import url_for
import re, locale, asyncio, jwt
from datetime import datetime, timedelta

locale.setlocale(locale.LC_TIME, "ru_RU")

app = create_app()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=ChatAction.TYPING)
    query = update.callback_query
    await query.answer()
    command = query.data
    match = re.match(r'/order (\d+)', command)
    if match:
        order_number = match.group(1)
        telegram_id = query.from_user.id
        user = next((user for user in Config.users if user['telegram_id'] == str(telegram_id)), None)
        if user is not None:
            user_id = user['user_id']
        else:
            return
        with app.app_context():
            order = Order.query.filter(Order.id == order_number).first()
            if not order:
                return await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Заказ удален!',
                parse_mode='HTML'
            )
            if str(order.manufacturer_id) != user['user_id'] and user['role'] != '1':
                return await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Это не ваш заказ',
                parse_mode='HTML'
            )
            context.user_data['current_order_id'] = order.id
            from app.routes.utils.old import old
            old(order.id, user_id)
            date = format_date(order.date, format='d MMMM', locale='ru_RU')
            month_cases = {
                "январь": "января",
                "февраль": "февраля",
                "март": "марта",
                "апрель": "апреля",
                "май": "мая",
                "июнь": "июня",
                "июль": "июля",
                "август": "августа",
                "сентябрь": "сентября",
                "октябрь": "октября",
                "ноябрь": "ноября",
                "декабрь": "декабря"
            }
            day, month = date.split()
            month_in_genitive = month_cases.get(month, month)
            date = f"{day} {month_in_genitive}"
            deadline = order.deadline.strftime("%A, %d.%m.%Y / %H:%M") if order.deadline else "Не назначено"
            desc = order.desc if order.desc != None and order.desc != '' else "Нет описания"
            try:
                previous_messages_ids = context.user_data.get('last_message_ids', [])
                if previous_messages_ids:
                    await delete_messages(update.effective_chat.id, context.bot, previous_messages_ids)
            except:
                pass
            SECRET_KEY = 'unknown'
            header = {
                'alg': 'HS256',
                'typ': 'JWT'
            }
            payload = {
                'user_id': str(user['user_id']),
                'role': str(user['role']),
                'order_id': str(order.id),
                'exp': datetime.now() + timedelta(days=1)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256', headers=header)
            url = url_for('main.comments', token=token)
            keyboard = [
                [InlineKeyboardButton("Комментарии", url=url)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            user = next((user for user in Config.users if user['telegram_id'] == str(telegram_id)), None)
            photo_count = f'\n\n📷 {len(order.photos)} фото прикреплено к заказу\n       *дождитесь их загрузки*' if len(order.photos) > 0 else ''
            comments = order.comments
            comments = Comment.query.filter(Comment.user_id != 0).filter(Comment.order_id == order.id).all()
            comment_count = f'\n\n💬 Комментарии: {len(comments)} шт' if len(comments) > 0 else ''
            doplata = f"{int(order.doplata):,}".replace(',', ' ') + " ₽" if order.doplata else 'Не указано'
            izgotovlenie = f"{int(order.izgotovlenie):,}".replace(',', ' ') + " ₽" if order.izgotovlenie else 'Не указано'
            montaj = f"{int(order.montaj):,}".replace(',', ' ') + " ₽" if order.montaj else 'Не указано'
            lift = "Большой" if order.lift == 1 else "Маленький" if order.lift == 2 else "Не указан"
            if user['role'] == '1':
                manufacturer = order.manufacturer.name if order.manufacturer_id else 'Не назначен'
                price = f"{int(order.price):,}".replace(',', ' ') + " ₽" if order.price else 'Не указано'
                prepayment = f"{int(order.prepayment):,}".replace(',', ' ') + " ₽" if order.prepayment else 'Не указано'
                message = f'<b>Заказ от {date} ({order.status.name})</b>\n\n👤 Заказчик: <b>{order.customer}</b>\n\n📱 Номер телефона: <b><a href="tel:{order.phone}">{order.phone}</a></b> <a href="https://wa.me/{order.phone}">💬 WhatsApp</a>\n\n🏠 Адрес: <b><a href="https://yandex.ru/maps/?text={urllib.parse.quote(order.address)}">{order.address}</a></b>\n\n↕️ Лифт: <b>{lift}</b>\n\n💵Доплата: <b>{doplata}</b>\n💵Изготовление: <b>{izgotovlenie}</b>\n💵Монтаж: <b>{montaj}</b>\n\n📅 Назначенная дата: <b>{deadline}</b>\n\n👷 Исполнитель: <b>{manufacturer}</b>\n\n📄 Описание:\n\n<b><blockquote>{desc}</blockquote>{comment_count}{photo_count}</b>'
            else:
                message = f'<b>Заказ от {date} ({order.status.name})</b>\n\n👤 Заказчик: <b>{order.customer}</b>\n\n📱 Номер телефона: <b><a href="tel:{order.phone}">{order.phone}</a></b> <a href="https://wa.me/{order.phone}">💬 WhatsApp</a>\n\n🏠 Адрес: <b><a href="https://yandex.ru/maps/?text={urllib.parse.quote(order.address)}">{order.address}</a></b>\n\n↕️ Лифт: <b>{lift}</b>\n\n💵Доплата: <b>{doplata}</b>\n💵Изготовление: <b>{izgotovlenie}</b>\n💵Монтаж: <b>{montaj}</b>\n\n📅 Назначенная дата: <b>{deadline}</b>\n\n📄 Описание:\n\n<b><blockquote>{desc}</blockquote>{comment_count}{photo_count}</b>'
            new_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            new_message_ids = [new_message.message_id]
            photos = []
            for photo in order.photos:
                photos.append(InputMediaPhoto(open(f'app/static/photo/{photo.path}', 'rb')))
            batch_size = 10
            for i in range(0, len(photos), batch_size):
                await context.bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
                media_group = await context.bot.send_media_group(
                    chat_id=update.effective_chat.id,
                    media=photos[i:i+batch_size]
                )
                new_message_ids.extend([msg.message_id for msg in media_group])
            context.user_data['last_message_ids'] = new_message_ids

async def delete_messages(chat_id, bot, message_ids):
    tasks = []
    for message_id in message_ids:
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=message_id))
    await asyncio.gather(*tasks)