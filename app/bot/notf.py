from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from app.routes.utils.mask_price import mask_price_and_prepayment
from config import Config

async def send_notification(user_id, message, order_id, adm, button = True):
    bot = Bot(token='7615618767:AAEqVUmQ4ML_G6u5C-VNUoNRlppuiiGtdYQ')
    user = next((user for user in Config.users if user['user_id'] == str(user_id)), None)
    admin_ids = [user['telegram_id'] for user in Config.users if user['role'] == '1']
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Перейти к заказу', callback_data=f'/order {order_id}')]])
    if adm:
        for admin_id in admin_ids:
            try:
                if button:
                    await bot.send_message(chat_id=admin_id,
                                        text=message,
                                        parse_mode='HTML',
                                        disable_web_page_preview=True,
                                        reply_markup=reply_markup)
                else:
                    await bot.send_message(chat_id=admin_id,
                                        text=message,
                                        parse_mode='HTML',
                                        disable_web_page_preview=True)
            except:
                pass
    if not adm:
        try:
            if user['role'] != '1':
                await bot.send_message(chat_id=user['telegram_id'],
                                       text=message,
                                       parse_mode='HTML',
                                       disable_web_page_preview=True,
                                       reply_markup=reply_markup)
        except:
            pass
    else:
        pass