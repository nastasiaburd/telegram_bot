
import os
import sys
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# ---------------- Логирование ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- Этапы разговора ----------------
NAME, APARTMENT, QUESTIONS, BREAKAGE, PHOTO_DESC = range(5)

# ---------------- Данные ----------------
apartments = [
    "9к3-27", "9к3-28", "9к3-29", "9к3-78", "13-51", "11с1-347", "5.-4",
    "42-1", "42-52", "42-105", "42-144", "3-174", "3-334", "3-852",
    "69к5-138", "7к1-348", "73к5-751", "73к5-752"
]

questions_list = [
    "Протерла на сухо ванну?",
    "Положила туалетную бумагу?",
    "Помыла дверной коврик?"
]

# ---------------- Команды бота ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пожалуйста, введи фамилию и имя:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    context.user_data['questions'] = {}
    context.user_data['question_index'] = 0

    keyboard = [[KeyboardButton(a)] for a in apartments]
    await update.message.reply_text(
        "Выбери квартиру:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return APARTMENT

async def get_apartment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['apartment'] = update.message.text
    await update.message.reply_text(
        questions_list[0] + " (напиши 'сделала' или 'не сделала')",
        reply_markup=None
    )
    return QUESTIONS

async def get_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['question_index']
    answer = update.message.text.lower()

    if answer not in ['сделала', 'не сделала']:
        await update.message.reply_text("Пожалуйста, ответь 'сделала' или 'не сделала'")
        return QUESTIONS

    context.user_data['questions'][questions_list[index]] = answer
    index += 1

    if index < len(questions_list):
        context.user_data['question_index'] = index
        await update.message.reply_text(
            questions_list[index] + " (напиши 'сделала' или 'не сделала')"
        )
        return QUESTIONS
    else:
        await update.message.reply_text("Были ли поломки в квартире? (да/нет)")
        return BREAKAGE

async def get_breakage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.lower()
    if answer not in ['да', 'нет']:
        await update.message.reply_text("Пожалуйста, ответь 'да' или 'нет'")
        return BREAKAGE

    context.user_data['breakage'] = answer
    if answer == 'да':
        await update.message.reply_text("Пожалуйста, пришли фото поломки или описание:")
        return PHOTO_DESC
    else:
        await update.message.reply_text(
            "Спасибо! Данные сохранены:\n" + str(context.user_data)
        )
        return ConversationHandler.END

async def get_photo_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
        await update.message.reply_text("Фото получено. Теперь пришли описание поломки.")
        return PHOTO_DESC
    elif update.message.text:
        context.user_data['description'] = update.message.text
        await update.message.reply_text(
            "Спасибо! Данные сохранены:\n" + str(context.user_data)
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, пришли фото или текст описания.")
        return PHOTO_DESC

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# ---------------- Основная функция ----------------
def main():
    # ---------------- Переменные окружения ----------------
    TOKEN = os.environ.get('TOKEN')
    APP_NAME = os.environ.get('APP_NAME')
    PORT = int(os.environ.get('PORT', 8443))

    if not TOKEN:
        logger.error("TOKEN не найден! Проверь Environment Variables на Render.")
        sys.exit(1)
    if not APP_NAME:
        logger.error("APP_NAME не найден! Проверь Environment Variables на Render.")
        sys.exit(1)

    logger.info(f"Переменные окружения найдены. APP_NAME={APP_NAME}")

    # ---------------- Создание приложения ----------------
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            APARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_apartment)],
            QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_questions)],
            BREAKAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_breakage)],
            PHOTO_DESC: [MessageHandler(filters.TEXT | filters.PHOTO, get_photo_desc)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)

    # ---------------- Запуск webhook ----------------
    app.run_webhook(
        listen='0.0.0.0',
        port=PORT,
        url_path=TOKEN,
        webhook_url=f'https://{APP_NAME}.onrender.com/{TOKEN}'
    )

if __name__ == '__main__':
    main()
