import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from google import genai
from google.genai import types

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Muhit o'zgaruvchilarini tekshirish
TELEGRAM_BOT_TOKEN = os.getenv("8671816486:AAHTmwW0ttN1a0SitvMNLb-BgIqT7xH8owQ")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6I0Q8biDwdCaA8W6IgKVr0iwLxi8NaeWyqkSITiiJIAaA")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_BOT_TOKEN va GEMINI_API_KEY muhit o'zgaruvchilarida berilishi shart!")

# Gemini Mijozini yaratish (GEMINI_API_KEY o'zgaruvchisini avtomatik o'qiydi)
client = genai.Client()

# Telegram tugmalari
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("ℹ️ Bot haqida")],
        [KeyboardButton("🌾 Qishloq xo'jaligi bo'yicha savol")],
    ],
    resize_keyboard=True,
)

SYSTEM_INSTRUCTION = """
Siz qishloq xo'jaligi, agrotexnologiyalar, qishloq ekinlari va chorvachilik bo'yicha tajribali mutaxassissiz.
Sizning vazifangiz FAQAT VA FAQAT quyidagi mavzularda foydalanuvchilarga professional, aniq va tushunarli maslahatlar berish:
1. Agrotexnologiya va zamonaviy dehqonchilik usullari.
2. Qishloq xo'jaligi ekinlari (ekish, parvarishlash, kasalliklar, hosilni yig'ish).
3. Chorvachilik (qoramol, qo'y-echki, parranda, ularni boqish, parvarish qilish va kasalliklaridan davolash).

AGAR foydalanuvchi qishloq xo'jaligi, agrotexnologiya yoki chorvachilikka aloqador BO'LMAGAN boshqa har qanday mavzuda savol bersa, unga xushmuomalalik bilan:
"Kechirasiz, men faqat agrotexnologiya, qishloq ekinlari va chorvachilik bo'yicha savollarga javob bera olaman. Iltimos, shu sohalarga oid savol bering." deb javob bering va boshqa ma'lumot bermang.
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start buyrug'i uchun javob."""
    welcome_text = (
        "Assalomu alaykum! 🌾\n\n"
        "Men Agrotexnologiya, Qishloq ekinlari va Chorvachilik bo'yicha yordamchi AI botman.\n"
        "Savolingizni yuborishingiz yoki pastdagi tugmalardan foydalanishingiz mumkin."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_KEYBOARD)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchidan kelgan xabarlarni qayta ishlash."""
    user_text = update.message.text.strip()

    # Tugmalar bosilganda
    if user_text == "ℹ️ Bot haqida":
        about_text = (
            "🤖 **Bot haqida:**\n\n"
            "Ushbu bot Sun'iy Intellekt (Google Gemini) texnologiyasi asosida ishlaydi.\n"
            "Bot faqat quyidagi yo'nalishlarda yordam bera oladi:\n"
            "• Agrotexnologiyalar\n"
            "• Qishloq xo'jaligi ekinlarini yetishtirish va parvarishlash\n"
            "• Chorvachilik va parrandachilik\n\n"
            "Savolingizni matn shaklida yozib yuboring!"
        )
        await update.message.reply_text(about_text, parse_mode="Markdown")
        return

    if user_text == "🌾 Qishloq xo'jaligi bo'yicha savol":
        await update.message.reply_text(
            "Marhamat, o'zingizni qiziqtirgan ekin, agrotexnologiya yoki chorva bo'yicha savolingizni yozing."
        )
        return

    # Gemini AI'ga so'rov yuborish (Rasmdagi yangi API va model bo'yicha)
    try:
        await update.message.chat.send_action("typing")

        response = client.interactions.create(
            model="gemini-3.8-flash",
            input=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,
            ),
        )

        reply_text = response.text if hasattr(response, 'text') and response.text else "Javob olishda xatolik yuz berdi."
        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"Gemini API xatoligi: {e}")
        await update.message.reply_text("Kechirasiz, javob tayyorlashda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.")

def main() -> None:
    """Botni ishga tushirish."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()