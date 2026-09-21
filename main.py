import os
import logging
import asyncio
from aiohttp import web
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

# Gemini client yaratish
client = genai.Client(api_key=GEMINI_API_KEY)

# Tugmalar klaviaturasi
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("ℹ️ Bot haqida")],
        [KeyboardButton("🌾 Qishloq xo'jaligi bo'yicha savol")],
    ],
    resize_keyboard=True,
)

SYSTEM_INSTRUCTION = """
Siz Andijon qishloq xo'jaligi va agrotexnologiyalar instituti tomonidan ishlab chiqilgan Agrar AI yordamchisiz.
Sizning vazifangiz FAQAT quyidagi mavzularda foydalanuvchilarga professional, aniq va tushunarli maslahatlar berish:
1. Agrotexnologiya va zamonaviy dehqonchilik usullari.
2. Qishloq xo'jaligi ekinlari (ekish, parvarishlash, kasalliklar va zararkunandalarga qarshi kurashish, hosilni yig'ish).
3. Chorvachilik (qoramol, qo'y-echki, parranda, ularni boqish, parvarish qilish va kasalliklarini davolash).

AGAR foydalanuvchi qishloq xo'jaligi, agrotexnologiya yoki chorvachilikka aloqador BO'LMAGAN boshqa har qanday mavzuda savol bersa, unga xushmuomalalik bilan:
"Kechirasiz, men faqat agrotexnologiya, qishloq ekinlari va chorvachilik bo'yicha savollarga javob bera olaman. Iltimos, shu sohalarga oid savol bering." deb javob bering va boshqa ma'lumot bermang.
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start buyrug'i uchun javob."""
    welcome_text = (
        "Assalomu alaykum! 🌾\n\n"
        "Men **Agrar AI** yordamchisiman. Andijon qishloq xo'jaligi va agrotexnologiyalar instituti "
        "tomonidan sizga qishloq xo'jaligi, agrotexnologiyalar, ekinlar parvarishi va chorvachilik bo'yicha ishonchli va ilmiy ma'lumot beraman.\n\n"
        "O'zingizni qiziqtirgan savolni yozib yuboring yoki quyidagi tugmalardan foydalaning:"
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi xabarlariga javob berish."""
    user_text = update.message.text.strip()

    if user_text == "ℹ️ Bot haqida":
        about_text = (
            "🤖 **Bot haqida:**\n\n"
            "Ushbu bot **Agrar AI** bo'lib, Andijon qishloq xo'jaligi va agrotexnologiyalar instituti tomonidan taqdim etilgan.\n\n"
            "Bot quyidagi sohalarda yordam bera oladi:\n"
            "• Agrotexnologiyalar va dehqonchilik\n"
            "• Qishloq xo'jaligi ekinlari parvarishi hamda kasalliklarga qarshi kurash\n"
            "• Chorvachilik, parrandachilik va ularni boqish\n\n"
            "Savolingizni matn shaklida yozib yuborishingiz mumkin!"
        )
        await update.message.reply_text(about_text, parse_mode="Markdown")
        return

    if user_text == "🌾 Qishloq xo'jaligi bo'yicha savol":
        await update.message.reply_text(
            "Marhamat, o'zingizni qiziqtirgan ekin, agrotexnologiya yoki chorvachilik bo'yicha savolingizni yozib yuboring."
        )
        return

    try:
        await update.message.chat.send_action("typing")

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.3,
                ),
            ),
        )

        reply_text = response.text if response.text else "Javob olishda xatolik yuz berdi."
        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"Gemini API xatoligi: {e}")
        await update.message.reply_text("Kechirasiz, javob tayyorlashda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.")

# Render portini ushlab turish uchun HTTP Server
async def handle_ping(request):
    return web.Response(text="Bot is running active on Render Free Web Service!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render avtomatik beradigan PORT o'zgaruvchisi (standart: 10000)
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Dummy HTTP server {port}-portda ishga tushdi.")

async def main_async():
    # Dumb Web server va Telegram Botni birga ishga tushirish
    await start_web_server()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot ishga tushdi...")
        # Cheksiz davom ettirish
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main_async())
