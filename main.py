import os
import asyncio
from io import BytesIO
from threading import Thread
from flask import Flask
from PyPDF2 import PdfReader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# API kalitlar
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN yoki GEMINI_API_KEY Render Environment Variables'da topilmadi!")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# PDF ma'lumotlar bazasi
pdf_database = {}

# Tizim yo'riqnomasi (ixchamlashtirilgan, AI tezroq qayta ishlashi uchun)
SYSTEM_INSTRUCTION = """
Siz Andijon qishloq xo'jaligi va agrotechnologiyalar institutining AI assistentisiz.
Qoidalar:
1. O'zingizni har doim institut assistenti deb tanishtiring (Gemini AI demang).
2. Faqat qishloq xo'jaligi, ekinlar, chorvachilik, agrotexnologiyalar va institut faoliyatiga oid savollarga javob bering.
3. Boshqa mavzular bo'lsa, muloyimlik bilan faqat agrar sohada yordam bera olishingizni ayting.
4. Javoblaringiz londa, aniq va tushunarli bo'lsin.
"""

app = Flask(__name__)

@app.route('/')
def home():
    return "Andijon QXAI Bot muvaffaqiyatli ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Assalomu alaykum!\n\n"
        "Men **Andijon qishloq xo'jaligi va agrotechnologiyalar instituti**ning sun'iy intellekt assistentiman.\n"
        "Qishloq xo'jaligi va institutimiz bo'yicha savollaringizni berishingiz mumkin.\n\n"
        "Shuningdek, PDF kitob yuklasangiz, undan foydalanib javob beraman!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document.mime_type == 'application/pdf':
        sent_msg = await update.message.reply_text("PDF fayl qabul qilindi. O'qilmoqda...")
        try:
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            pdf_reader = PdfReader(BytesIO(file_bytes))
            extracted_text = ""
            for page in pdf_reader.pages[:50]:  # Tezlik uchun dastlabki 50 sahifagacha chegaralandi
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            
            user_id = update.message.from_user.id
            pdf_database[user_id] = f"\n--- {document.file_name} ---\n" + extracted_text[:15000]
            
            await sent_msg.edit_text(f"<b>{document.file_name}</b> xotiraga saqlandi! Savolingizni berishingiz mumkin.", parse_mode="HTML")
        except Exception as e:
            await sent_msg.edit_text(f"PDF faylni o'qishda xatolik: {str(e)}")
    else:
        await update.message.reply_text("Iltimos, faqat PDF formatidagi fayl yuboring.")

# AI so'rovini асинхрон (фонда) bajarish funksiyasi (Bot qotib qolmasligi uchun)
def call_gemini_api(model_name, prompt):
    return gemini_client.models.generate_content(
        model=model_name,
        contents=prompt
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    sent_message = await update.message.reply_text("O'ylanmoqda...")

    context_data = ""
    if user_id in pdf_database:
        context_data = f"\n\nPDF ma'lumotlari:\n{pdf_database[user_id][:4000]}"

    full_prompt = f"{SYSTEM_INSTRUCTION}\n{context_data}\n\nSavol: {user_text}"

    # Birinchi navbatda eng tezkor va barqaror model ishlatiladi
    models_to_try = ['gemini-1.5-flash', 'gemini-3.6-flash']
    
    success = False
    last_error = ""
    loop = asyncio.get_running_loop()
    
    for model_name in models_to_try:
        try:
            # API сўровини ижрочи оқида (thread) юбориш — Telegram ботни ушлаб қолмайди
            response = await loop.run_in_executor(None, call_gemini_api, model_name, full_prompt)
            await sent_message.edit_text(response.text)
            success = True
            break
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "RESOURCE_EXHAUSTED" in last_error or "404" in last_error:
                continue
            if "503" in last_error or "UNAVAILABLE" in last_error:
                await asyncio.sleep(1)  # time.sleep o'rniga asinxron kutish
                continue

    if not success:
        await sent_message.edit_text("Hozirda Google AI serverlari band yoki kunlik limit tugadi. Birozdan so'ng qayta urinib ko'ring!")

def main():
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Andijon QXAI Boti tezkor rejimda ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
