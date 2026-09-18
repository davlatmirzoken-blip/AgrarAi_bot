import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from openai import AsyncOpenAI
from rapidfuzz import process, fuzz
from aiohttp import web

# Kalitlarni o'zgaruvchilarga olish
BOT_TOKEN = os.getenv("BOT_TOKEN", "8991596787:AAFupK5TrDV9LB_L7ESAmIkJwOptFb2Oc34")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")

# Bot va OpenAI klientini ishga tushirish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

# Kalit so'zlarni xatoliklar bilan moslashtirish uchun lug'at
KEYWORDS = {
    "start": ["start", "boshlash", "stard", "stat", "boshla"],
    "help": ["yordam", "yordam ber", "xelp", "help", "yordamne"]
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
        "Men OpenAI (ChatGPT) va aqlli qidiruv tizimi bilan ishlayman. "
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

    wait_msg = await message.answer("⏳ ChatGPT tahlil qilmoqda, iltimos kuting...")

    system_instruction = (
        "Siz Oʻzbekiston qishloq xoʻjaligi, tuproq-iqlim sharoiti va ekin navlari boʻyicha professional agronom AI ekspertisiz. "
        "Foydalanuvchi matnda harfiy xatolar qilgan boʻlsa ham uning maqsadi va mazmunini toʻgʻri anglab, "
        "Oʻzbekiston yerlaridan unumli foydalanish va yuqori sifatli ekin yetishtirish boʻyicha aniq, ilmiy va tushunarli javob bering."
    )

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Tejamkor va juda tez model
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_text}
            ],
            temperature=0.5
        )
        ai_reply = response.choices[0].message.content
        await wait_msg.delete()
        await message.answer(ai_reply, parse_mode="Markdown")
    except Exception as e:
        await wait_msg.delete()
        await message.answer(f"Xatolik yuz berdi: {str(e)}")

# Render Web Service uchun portni ochiq tutuvchi yengil HTTP server
async def handle_health_check(request):
    return web.Response(text="Agrar AI Bot (OpenAI) muvaffaqiyatli ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web-server port {port} da ishga tushdi.")

async def main():
    print("Bot va Web-server ishga tushmoqda...")
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
