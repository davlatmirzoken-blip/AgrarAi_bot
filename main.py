import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from google import genai
from rapidfuzz import process, fuzz

BOT_TOKEN = os.getenv("8991596787:AAFupK5TrDV9LB_L7ESAmIkJwOptFb2Oc34")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6KyGENeMae18dCvtFc7qo8ToT2mOSwrQeZZQwSUBH7c_A")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
ai_client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO)

KEYWORDS = {
    "start": ["start", "boshlash", "stard", "stat"],
    "help": ["yordam", "yordam ber", "xelp", "help"]
}

def match_keyword(text: str) -> str:
    text_lower = text.lower().strip()
    for key, values in KEYWORDS.items():
        best_match = process.extractOne(text_lower, values, scorer=fuzz.ratio)
        if best_match and best_match[1] >= 70:
            return key
    return "ai_query"

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🌱 **Oʻzbekiston Qishloq Xoʻjaligi AI Yordamchisiga xush kelibsiz!**\n\n"
        "Men Google Gemini AI va aqlli qidiruv tizimi bilan ishlayman. "
        "Harfiy xatolar bilan yozsangiz ham sizni tushunaman!\n\n"
        "Menga oʻzingizni qiziqtirgan savolni, hudud va ekin haqida yozing."
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(F.text)
async def handle_all_messages(message: types.Message):
    user_text = message.text
    matched_intent = match_keyword(user_text)

    if matched_intent == "start":
        await cmd_start(message, None)
        return
    elif matched_intent == "help":
        await message.answer("Siz menga qishloq xoʻjaligi, yer turlari yoki ekin navlari boʻyicha xohlagan koʻrinishda savol berishingiz mumkin.")
        return

    wait_msg = await message.answer("⏳ Gemini AI tahlil qilmoqda, iltimos kuting...")

    system_instruction = (
        "Siz Oʻzbekiston qishloq xoʻjaligi, tuproq-iqlim sharoiti va ekin navlari boʻyicha professional agronom AI ekspertisiz. "
        "Foydalanuvchi matnda harfiy xatolar qilgan boʻlsa ham uning maqsadi va mazmunini toʻgʻri anglab, "
        "Oʻzbekiston yerlaridan unumli foydalanish va yuqori sifatli ekin yetishtirish boʻyicha aniq, ilmiy va tushunarli javob bering."
    )

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Foydalanuvchi soʻrovi: {user_text}",
            config={
                "system_instruction": system_instruction,
                "temperature": 0.5
            }
        )
        await wait_msg.delete()
        await message.answer(response.text, parse_mode="Markdown")
    except Exception as e:
        await wait_msg.delete()
        await message.answer(f"Xatolik yuz berdi: {str(e)}")

async def main():
    print("Bot Gemini AI bilan ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
