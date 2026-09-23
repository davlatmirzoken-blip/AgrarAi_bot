import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# API kalitlarni muhit o'zgaruvchilaridan (Environment Variables) olish
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini mijozini sozlash
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Render Web Service uchun kichik Flask server (Sog'lomlikni tekshirish)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Telegram /start buyrug'iga javob
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Men Gemini AI bilan ishlaydigan botman. Savolingizni yuboring!")

# Xabarlarni Gemini AI orqali qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Kutish xabari
    sent_message = await update.message.reply_text("O'ylanmoqda...")

    try:
        # Gemini modeliga so'rov yuborish
        response = gemini_client.models.generate_content(
            model='gemini-3.6-flash',
            contents=user_text,
        )
        await sent_message.edit_text(response.text)
    except Exception as e:
        await sent_message.edit_text(f"Xatolik yuz berdi: {str(e)}")

def main():
    # Flask serverni alohida oqimda (thread) ishga tushirish
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    # Telegram botni ishga tushirish
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
