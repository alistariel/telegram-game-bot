import logging
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)

def load_questions(sheet_url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).sheet1
    data = sheet.get_all_records()

    questions = {"один": [], "с компанией": []}
    for row in data:
        category = row.get("Категория", "").strip().lower()
        question = row.get("Вопрос", "").strip()
        if category in questions:
            questions[category].append(question)
    return questions

QUESTIONS = load_questions("https://docs.google.com/spreadsheets/d/1MXtCN5d8kFHFrY6UC0doEvLhzNuzqqamL6b7FDtf33M/edit?usp=drivesdk")
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Нажми «Старт», чтобы начать.")

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Выбери категорию вопросов: для игры в паре или компании и для игры с самим собой"
    keyboard = [["С компанией", "Один"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=markup)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    user_id = update.effective_user.id

    if user_input in ["один", "с компанией"]:
        user_state[user_id] = user_input
        markup = ReplyKeyboardMarkup([["Начать игру"]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"Категория «{user_input}» выбрана. Готов?", reply_markup=markup)

    elif user_input == "начать игру":
        category = user_state.get(user_id)
        if not category:
            await update.message.reply_text("Сначала выбери категорию.")
            return
        if category not in QUESTIONS or not QUESTIONS[category]:
            await update.message.reply_text("В этой категории пока нет вопросов.")
            return
        question = random.choice(QUESTIONS[category])
        await update.message.reply_text(f"Вопрос: {question}")
    else:
        await update.message.reply_text("Пожалуйста, выбери категорию или нажми «Начать игру».")

if __name__ == "__main__":
    import os
    TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^старт$"), handle_start_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice))

    app.run_polling()
