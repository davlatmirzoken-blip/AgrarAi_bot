import os
import time
import asyncio
from io import BytesIO
from threading import Thread
from Flask import Flask
from PyPDF2 import PdfReader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# API kalitlar
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# PDF fayllardan olingan matnlarni xotirada (bazada) saqlash uchun lug'at
pdf_database = {}

# System Prompt - Botning shaxsiyati va vazifasi
SYSTEM_INSTRUCTION = """
Siz Andijon qishloq xo'jaligi va agrotechnologiyalar institutining rasmiy sun'iy intellekt assistentisiz.
Sizning vazifangiz va qoidalaringiz:
1. Hech qachon "Men Gemini AI'man" deb aytmang. Har doim o'zingizni Andijon qishloq xo'jaligi va agrotechnologiyalar institutining AIsi sifatida tanishtiring.
2. Institut haqida so'rashsa: Andijon qishloq xo'jaligi va agrotechnologiyalar instituti Farg'ona vodiysida va mamlakatimizda agrar sohada yetuk mutassislar, agronomlar va veterinarlarni tayyorlaydigan yetakchi oliy ta'lim muassasasi ekanligini faxr bilan ayting.
3. Siz FAQT qishloq xo'jaligi, ekinlar, dehqonchilik, chorvachilik, parrandachilik, agrotexnologiyalar va veterinariya mavzularida javob berasiz.
4. Agar foydalanuvchi qishloq xo'jaligiga aloqador bo'lmagan (masalan: dasturlash, kino, siyosat va h.k.) savol bersa, muloyimlik bilan faqat qishloq xo'jaligi va institut faoliyatiga oid savollarga javob bera olishingizni ayting.
"""

# Render uchun Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return "Andijon QXAI Bot muvaffaqiyatli ishlamoqda!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Assalomu alaykum!\n\n"
        "Men **Andijon qishloq xo'jaligi va agrotechnologiyalar instituti**ning sun'iy intellekt assistentiman. "
        "Qishloq xo'jaligi, ekinlar parvarishi, chorvachilik va institutimiz haqidagi barcha savollaringizga javob beraman.\n\n"
        "Shuningdek, menga kitob yoki qo'llanma (PDF fayl) yuborsangiz, uni bazamga saqlab olaman va undagi ma'lumotlar bo'yicha savollaringizga javob beraman!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# PDF fayllarni qabul qilish va matnni ajratib bazaga saqlash
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if document.mime_type == 'application/pdf':
        sent_msg = await update.message.reply_text("PDF fayl qabul qilindi. Ma'lumotlar bazaga yuklanmoqda...")
        try:
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            # PDF matnini o'qish
            pdf_reader = PdfReader(BytesIO(file_bytes))
            extracted_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            
            user_id = update.message.from_user.id
            if user_id not in pdf_database:
                pdf_database[user_id] = ""
            
            # Bazaga yangi kitob matnini qo'shish
            pdf_database[user_id] += f"\n--- {document.file_name} ---\n" + extracted_text
            
            await sent_msg.edit_text(f" '<b>{document.file_name}</b>' muvaffaqiyatli o'qildi va xotiraga saqlandi! Endi ushbu kitob bo'yicha savol berishingiz mumkin.", parse_mode="HTML")
        except Exception as e:
            await sent_msg.edit_text(f"PDF faylni o'qishda xatolik yuz berdi: {str(e)}")
    else:
        await update.message.reply_text("Iltimos, faqat PDF formatidagi fayllarni yuboring.")

# Matnli xabarlarni qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    sent_message = await update.message.reply_text("O'ylanmoqda...")

    # Agar foydalanuvchi PDF yuklagan bo'lsa, uni kontekstga qo'shish
    context_data = ""
    if user_id in pdf_database:
        context_data = f"\n\nFoydalanuvchi yuklagan PDF kitoblar/baza ma'lumotlari:\n{pdf_database[user_id][:10000]}" # Belgi chekloviga moslash

    full_prompt = f"{SYSTEM_INSTRUCTION}\n{context_data}\n\nFoydalanuvchi savoli: {user_text}"

    # 503 va boshqa vaqtinchalik xatoliklarda 3 marta qayta urinish logikasi
    for attempt in range(3):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt,
            )
            await sent_message.edit_text(response.text)
            break
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < 2:
                time.sleep(2)
                continue
            await sent_message.edit_text(f"Xatolik yuz berdi yoki server band. Qayta urinib ko'ring.\nBatafsil: {str(e)}")
            break

def main():
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Andijon QXAI Boti ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
