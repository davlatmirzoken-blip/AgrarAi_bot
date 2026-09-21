import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from google import genai
from aiohttp import web

# Kalitlarni olish
BOT_TOKEN = os.getenv("8671816486:AAHTmwW0ttN1a0SitvMNLb-BgIqT7xH8owQ")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6JPADhqqBHkv3bnhTNTcNlmJBq5wNVrtsa3kQi1-JOi4Q")

# Yangi Gemini SDK
client = genai.Client(api_key=GEMINI_API_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Assalomu alaykum! Men Gemini AI bilan ishlaydigan botman. Savol bering!")

@dp.message()
async def ai_handler(message: types.Message):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.text,
        )
        await message.answer(response.text)
    except Exception as e:
        await message.answer("Xatolik yuz berdi, iltimos qaytadan urinib ko'ring.")

# Render Web Service o'chib qolmasligi uchun kichik dummy-server
async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

async def main():
    # Render beradigan PORT-ni tinglash
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    # Telegram bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
