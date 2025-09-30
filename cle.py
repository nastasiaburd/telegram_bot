from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# Этапы разговора
NAME, APARTMENT, QUESTIONS, BREAKAGE, PHOTO_DESC = range(5)

# Список квартир
apartments = [
    "9к3-27", "9к3-28", "9к3-29", "9к3-78", "13-51", "11с1-347", "5.-4", 
    "42-1", "42-52", "42-105", "42-144", "3-174", "3-334", "3-852", 
    "69к5-138", "7к1-348", "73к5-751", "73к5-752"
]

# Список вопросов о горничной
questions_list = [
    "Протерла на сухо ванну?", 
    "Положила туалетную бумагу?", 
    "Помыла дверной коврик?"
]

# Словарь для хранения данных пользователя
user_data_dict = {}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пожалуйста, введи фамилию и имя:")
    return NAME

# Получение имени
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict['name'] = update.message.text
    # Клавиатура для выбора квартиры
    keyboard = [[KeyboardButton(a)] for a in apartments]
    await update.message.reply_text(
        "Выбери квартиру:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return APARTMENT

# Получение квартиры
async def get_apartment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_dict['apartment'] = update.message.text
    user_data_dict['questions'] = {}
    context.user_data['question_index'] = 0
    await update.message.reply_text(
        questions_list[0] + " (напиши 'сделала' или 'не сделала')",
        reply_markup=None
    )
    return QUESTIONS

# Вопросы о горничной
async def get_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data['question_index']
    answer = update.message.text.lower()
    if answer not in ['сделала', 'не сделала']:
        await update.message.reply_text("Пожалуйста, ответь 'сделала' или 'не сделала'")
        return QUESTIONS

    user_data_dict['questions'][questions_list[index]] = answer
    index += 1
    if index < len(questions_list):
        context.user_data['question_index'] = index
        await update.message.reply_text(questions_list[index] + " (напиши 'сделала' или 'не сделала')")
        return QUESTIONS
    else:
        await update.message.reply_text("Были ли поломки в квартире? (да/нет)")
        return BREAKAGE

# Поломки
async def get_breakage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.lower()
    if answer not in ['да', 'нет']:
        await update.message.reply_text("Пожалуйста, ответь 'да' или 'нет'")
        return BREAKAGE

    user_data_dict['breakage'] = answer
    if answer == 'да':
        await update.message.reply_text("Пожалуйста, пришли фото поломки и описание:")
        return PHOTO_DESC
    else:
        await update.message.reply_text("Спасибо! Данные сохранены:\n" + str(user_data_dict))
        return ConversationHandler.END

# Фото и описание поломки
async def get_photo_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        user_data_dict['photo'] = photo_file_id
    user_data_dict['description'] = update.message.text
    await update.message.reply_text("Спасибо! Данные сохранены:\n" + str(user_data_dict))
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Основная функция запуска
def main():
    app = ApplicationBuilder().token("8240812498:AAFHYTB-QhNdlT3U0aZUKA_N9qdiaYdz0q0").build()

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
    app.run_polling()

if __name__ == '__main__':
    main()
