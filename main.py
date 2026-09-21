import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import google.generativeai as genai

BOT_TOKEN = os.getenv("8991596787:AAG5r8-bQusCX4BSsQBvqEZAMuA5OBgrYRc")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6K9lkIAzcK-f9rMRRLHXxKRg-shPWNv55Uh50cODg4N8A")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Assalomu alaykum! Men Gemini AI bilan ishlaydigan botman. Menga savol bering!")

@dp.message()
async def ai_handler(message: types.Message):
    try:
        response = model.generate_content(message.text)
        await message.answer(response.text)
    except Exception as e:
        await message.answer("Xatolik yuz berdi, iltimos qaytadan urinib ko'ring.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
