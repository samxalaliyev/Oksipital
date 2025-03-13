# import os
# import json
# import requests
# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# # Telegram Bot Token'ını buraya ekleyin
# TELEGRAM_BOT_TOKEN = "7486287124:AAHwsf8A5MIQRKq9bEFRV0jSKsvzSEu1Lrw"
# AI_API_URL = "https://ai-text-to-image.yenitest.workers.dev/"  # Cloudflare Worker API URL

# async def start(update: Update, context: CallbackContext):
#     """Botun başlangıç mesajını gönderir."""
#     await update.message.reply_text("Merhaba! Bana bir kelime veya cümle gönder, yapay zeka ile bir görsel oluşturalım!")

# async def generate_image(update: Update, context: CallbackContext):
#     """Kullanıcının gönderdiği metni alır, API'ye istek yapar ve resmi gönderir."""
#     user_input = update.message.text

#     payload = {"prompt": user_input}
#     headers = {"Content-Type": "application/json"}

#     try:
#         response = requests.post(AI_API_URL, json=payload, headers=headers)

#         if response.status_code == 200:
#             result = response.json()
#             image_url = result.get("imageUrl", "")

#             if image_url:
#                 await update.message.reply_photo(photo=image_url, caption="İşte senin görselin! 🎨")
#             else:
#                 await update.message.reply_text("Görsel oluşturulamadı. Lütfen tekrar deneyin.")
#         else:
#             await update.message.reply_text("API'de bir hata oluştu. Daha sonra tekrar deneyin.")

#     except Exception as e:
#         await update.message.reply_text(f"Hata oluştu: {str(e)}")

# def main():
#     """Telegram botunu başlatır."""
#     app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

#     # Komutları ekleyelim
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

#     print("Bot çalışıyor...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()


#?============================================================================================================

# import io
# import requests
# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# # Telegram Bot Token'ınızı buraya ekleyin
# TELEGRAM_BOT_TOKEN = "7486287124:AAHwsf8A5MIQRKq9bEFRV0jSKsvzSEu1Lrw"

# # Cloudflare Worker API endpoint'iniz
# WORKER_ENDPOINT = "https://ai-text-to-image.yenitest.workers.dev/"

# async def start(update: Update, context: CallbackContext):
#     await update.message.reply_text("Merhaba! Lütfen bir prompt gönderin, görsel oluşturuluyor...")

# async def generate_image(update: Update, context: CallbackContext):
#     prompt = update.message.text
#     await update.message.reply_text("Görsel oluşturuluyor, lütfen bekleyin...")

#     try:
#         # Worker endpoint'ine POST isteği gönderiyoruz (JSON formatında prompt gönderiyoruz)
#         response = requests.post(WORKER_ENDPOINT, json={"prompt": prompt})
        
#         if response.status_code == 200:
#             # Yanıt binary veri (image/png) olarak geldiği için response.json() kullanamayız.
#             # Binary veriyi BytesIO ile Telegram'a gönderilebilir hale getiriyoruz.
#             image_bytes = response.content
#             bio = io.BytesIO(image_bytes)
#             bio.name = "generated.png"  # Dosya adı belirtiyoruz

#             await update.message.reply_photo(photo=bio)
#         else:
#             await update.message.reply_text("Serviste bir hata oluştu. Lütfen tekrar deneyin.")
#     except Exception as e:
#         await update.message.reply_text(f"Hata oluştu: {str(e)}")

# def main():
#     app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

#     print("Bot çalışıyor...")
#     app.run_polling()

# if __name__ == "__main__":
#     main()



#?============================================================================================================


import io
import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Konuşma durumu sabiti
SELECT_MODEL = 0

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Kullanıcının gönderdiği prompt'u alıp model seçimi için inline butonları gösteren giriş fonksiyonu
async def handle_prompt(update: Update, context: CallbackContext) -> int:
    prompt = update.message.text
    context.user_data['prompt'] = prompt
    keyboard = [
        [InlineKeyboardButton("Flux", callback_data="flux")],
        [InlineKeyboardButton("SDXL", callback_data="sdxl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Lütfen bir model seçin:", reply_markup=reply_markup)
    return SELECT_MODEL

# Inline butonlardan model seçildiğinde çalışacak fonksiyon
async def select_model(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    selected_model = query.data
    prompt = context.user_data.get('prompt')
    if not prompt:
        await query.edit_message_text("Prompt bulunamadı, lütfen tekrar deneyin.")
        return ConversationHandler.END
    await query.edit_message_text(f"Seçilen model: {selected_model.upper()}\nGörsel oluşturuluyor, lütfen bekleyin...")

    # Cloudflare Worker API endpoint'iniz
    WORKER_ENDPOINT = "https://ai-text-to-image.yenitest.workers.dev/"
    payload = {"prompt": prompt, "model": selected_model}
    
    try:
        response = requests.post(WORKER_ENDPOINT, json=payload)
        if response.status_code == 200:
            image_bytes = response.content
            bio = io.BytesIO(image_bytes)
            bio.name = "generated.jpg"
            await query.message.reply_photo(photo=bio)
        else:
            await query.message.reply_text(f"API hatası: {response.status_code}\n{response.text}")
    except Exception as e:
        logger.error(f"API isteği sırasında hata: {e}")
        await query.message.reply_text(f"Hata oluştu: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)],
        states={
            SELECT_MODEL: [CallbackQueryHandler(select_model)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)]
    )

    app.add_handler(conv_handler)
    logger.info("🚀 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()


  
