from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from app.bot.orders import orders
from app.bot.show import button_handler
from app.bot.textcomment import handle_text_comment
from app.bot.create import create, cancel, create_query
from app.bot.contentcomment import handle_media_group

def run_bot():
    application = ApplicationBuilder().token('7615618767:AAEqVUmQ4ML_G6u5C-VNUoNRlppuiiGtdYQ').build()
    
    application.add_handler(CommandHandler('orders', orders))
    # application.add_handler(CommandHandler('create', create))
    application.add_handler(CommandHandler('start', orders))
    application.add_handler(CallbackQueryHandler(combined_button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, combined_text_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_media_group))
    
    application.run_polling()

async def combined_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await button_handler(update, context)
    # await cancel(update, context)

async def combined_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_text_comment(update, context)
    # await create_query(update, context)